"""Shared fixtures: temp scenarios, FakeProvider, dev-header auth, TestClient."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kops.platform import Settings, create_app
from kops.platform.db import SessionRow
from kops.providers.fake import FakeProvider

SCENARIO_YAML = """\
apiVersion: kops/v1alpha1
kind: Scenario
id: {id}
revision: 1
title: Test scenario {id}
difficulty: {{level: {level}}}
tags: [test, {id}]
profiles:
  cka: {{enabled: true, domain: troubleshooting, primary_competency: CKA-TRB-05}}
  ckad: {{enabled: {ckad}, domain: services-networking, primary_competency: CKAD-SNW-02}}
backend: {{class: kind, topology: {{control_planes: 1, workers: 0}}}}
task:
  statement_file: task.md
  parameters:
    ns: {{type: dns-label, prefix: t-}}
setup:
  script: setup/setup.sh
  confirm: {{must_fail: [goal], must_pass: [guard]}}
verification:
  criteria_file: verify/criteria.yaml
  settle: {{max_wait_seconds: 0, poll_interval_seconds: 1}}
reset:
  strategy: destroy-cluster
{reset}
reference: {{solution: reference/solution.sh}}
"""
CRITERIA = """\
criteria:
  - id: goal_cm
    invariant: goal
    required: true
    check: {type: k8s.exists, resource: {kind: ConfigMap, name: fixed, namespace: "{{ns}}"}, expect: present}
  - id: guard_cm
    invariant: guard
    required: true
    check: {type: k8s.exists, resource: {kind: ConfigMap, name: keep, namespace: "{{ns}}"}, expect: present}
"""


def make_scenario(root: Path, sid: str, reset: str | None, hints: int, level: int = 1, ckad: bool = False):
    d = root / sid
    for sub in ("setup", "verify", "reference", "fixtures"):
        (d / sub).mkdir(parents=True)
    line = f"  mode: {reset}" if reset else ""
    (d / "scenario.yaml").write_text(SCENARIO_YAML.format(id=sid, level=level, ckad=str(ckad).lower(), reset=line))
    (d / "task.md").write_text("Fix the ConfigMap in namespace `{{ns}}`.\n")
    (d / "setup/setup.sh").write_text("true\n")
    (d / "verify/criteria.yaml").write_text(CRITERIA)
    (d / "reference/solution.sh").write_text("true\n")
    (d / "fixtures/cm.yaml").write_text("name: keep-{{ns}}\n")
    if hints:
        (d / "reference/hints.md").write_text("# Hints\n" + "".join(f"{i}. hint {i} for {{{{ns}}}}\n" for i in range(1, hints + 1)))
        (d / "reference/explanation.md").write_text("# Explanation\nCreate `fixed` in {{ns}}.\n")


def setup_hook(sb, script, env):
    ns = env["KOPS_P_NS"]
    sb.put("namespace", ns)
    sb.put("configmap", "keep", ns, data={"a": "b"})


@pytest.fixture
def scenarios(tmp_path):
    root = tmp_path / "scenarios"
    make_scenario(root, "t-api-a-001", "api", 3, level=2, ckad=True)
    make_scenario(root, "t-api-b-001", "api", 0)
    make_scenario(root, "t-vm-001", None, 3)
    return root


class Env:
    def __init__(self, tmp_path, scenarios, **over):
        self.provider = FakeProvider()
        self.provider.setup_hook = setup_hook
        kw = dict(db_url=f"sqlite:///{tmp_path}/t.db", provider="fake",
                  session_secret="x", scenarios_dir=scenarios, web_dir=tmp_path / "noweb",
                  allow_dev_auth=True, auth_mode="dev-header", sweep_interval_seconds=0,
                  sse_poll_seconds=0.05, reset_timeout_seconds=2, reset_poll_seconds=0.01) | over
        self.settings = Settings(**kw)
        self.app = create_app(self.settings, self.provider)
        self.client = TestClient(self.app)
        self.service = self.app.state.service

    @staticmethod
    def h(name="alice", admin=False):
        return {"X-Dev-User": name} | ({"X-Dev-Admin": "1"} if admin else {})

    def create(self, user="alice", scenario="t-api-a-001", **kw):
        body = {"type": "practice", "scenario_id": scenario} | kw
        return self.client.post("/api/sessions", json=body, headers=self.h(user))

    def get(self, sid, user="alice"):
        return self.client.get(f"/api/sessions/{sid}", headers=self.h(user)).json()

    def wait(self, sid, state, user="alice", timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            s = self.get(sid, user)
            if s["state"] == state:
                return s
            time.sleep(0.02)
        raise AssertionError(f"session {sid} stuck in {s['state']} ({s.get('message')}), wanted {state}")

    def active(self, user="alice", scenario="t-api-a-001", **kw):
        sid = self.create(user, scenario, **kw).json()["id"]
        return self.wait(sid, "ACTIVE", user)

    def sandbox(self, sid):
        with self.service.db.session() as s:
            row = s.get(SessionRow, sid)
        return self.provider.sandboxes[row.sandbox_id], json.loads(row.params_json)

    def solve(self, sid):
        sb, params = self.sandbox(sid)
        sb.put("configmap", "fixed", params["ns"])


@pytest.fixture
def env(tmp_path, scenarios):
    return Env(tmp_path, scenarios)
