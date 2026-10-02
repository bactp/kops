"""Needs docker + kind. Run with: KOPS_E2E=1 pytest -m e2e"""
import json
import os
import shlex
from pathlib import Path

import pytest

from kops.harness import ShellLoopAgent
from kops.models import ScriptedModel
from kops.runner import run_trial
from kops.scenario import load_scenario

S03 = Path(__file__).resolve().parents[1] / "scenarios" / "kops-net-service-endpoint-repair-001"
pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not os.environ.get("KOPS_E2E"), reason="set KOPS_E2E=1")]


def block(cmd):
    return f"```bash\n{cmd}\n```"


def test_shell_loop_on_real_cluster_with_errors_and_recovery(tmp_path):
    scn = load_scenario(S03, seed=11)
    ns, app, port = scn.namespace, scn.params["app"], scn.params["port"]
    patch = json.dumps({"spec": {"selector": {"app": app, "tier": "web"},
                                 "ports": [{"port": 80, "targetPort": port}]}})
    model = ScriptedModel([
        "Let me look around.",                                           # parse_error
        block("ls /"),                                                   # policy_rejected
        block(f"kubectl -n {ns} get svc,endpointslices"),                # ok
        block(f"kubectl -n {ns} get podz"),                              # invalid exec_error
        block(f"kubectl -n {ns} get pods --show-labels"),                # ok (recovery)
        block(f"kubectl -n {ns} patch service {app} --type merge -p {shlex.quote(patch)}"),
        "SUBMIT: selector and targetPort corrected",
    ])
    rec = run_trial(S03, ShellLoopAgent("scripted-model", model), seed=11, experiment="e2e",
                    trial_index=0, out_root=tmp_path)
    assert rec["outcome"] == "PASS", rec.get("invalid_reason") or rec["verifier"]
    m = rec["metrics"]
    assert (m["steps"], m["parse_errors"], m["policy_rejected"], m["invalid_actions"]) == (6, 1, 1, 3)
    assert m["mutating_steps"] == 1 and m["recovery_count"] >= 1 and rec["claim"]["submitted"]
    assert rec["reset"]["clean"]
    trace = [json.loads(l) for l in (Path(rec["_dir"]) / "trace.jsonl").read_text().splitlines()]
    assert [e["kind"] for e in trace if e["type"] == "action"][:3] == ["parse_error", "policy_rejected", "ok"]
