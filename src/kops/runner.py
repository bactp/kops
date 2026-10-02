"""Scenario Runner: orchestration only. No Kubernetes reasoning lives here.

LOAD -> PROVISION -> SETUP -> READY(confirm) -> RUN AGENT -> VERIFY -> COLLECT -> CLEANUP
"""
from __future__ import annotations

import hashlib
import subprocess
import time
import traceback
import uuid
from dataclasses import asdict
from pathlib import Path

from . import config
from .backend_kind import BackendError, KindCluster
from .gateway import Gateway, Trace
from .harness import AgentOutcome
from .models import ModelError
from .recorder import SCHEMA, auto_failure_labels, derive_metrics, write_trial
from .scenario import Scenario, load_scenario
from .verifier import FAIL, PASS, Verifier


class InvalidTrial(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


def _git_sha() -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(config.ROOT), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        dirty = subprocess.run(["git", "-C", str(config.ROOT), "status", "--porcelain", "src", "scenarios"],
                               capture_output=True, text=True, timeout=10).stdout.strip()
        return r.stdout.strip() + ("+dirty" if dirty else "")
    except Exception:
        return None


def _confirm_setup(scn: Scenario, ver: Verifier) -> dict:
    """Negative control: goals must FAIL before the agent acts; guards must PASS."""
    conf = scn.setup_confirm()
    res_fail = ver.evaluate(conf["must_fail"], settle=False)
    res_pass = ver.evaluate(conf.get("must_pass", []), settle=False)
    for r in res_fail + res_pass:
        if r.status == "error":
            raise InvalidTrial("verifier_error_at_confirm", f"{r.id}: {r.evidence}")
    not_failing = [r.id for r in res_fail if r.status != FAIL]
    not_passing = [r.id for r in res_pass if r.status != PASS]
    if not_failing or not_passing:
        raise InvalidTrial("setup_confirm_failed",
                           f"goals that already pass: {not_failing}; guards that fail: {not_passing}")
    return {"must_fail": [asdict(r) for r in res_fail], "must_pass": [asdict(r) for r in res_pass]}


def run_trial(scenario_dir: Path, agent, *, seed: int, experiment: str, trial_index: int,
              out_root: Path | None = None) -> dict:
    """Run one trial on a fresh cluster and return the trial record (also written to disk)."""
    started = time.time()
    scn = load_scenario(scenario_dir, seed)
    run_id = uuid.uuid4().hex[:8]
    trial_id = f"{agent.name}__{scn.id}__s{seed}__t{trial_index}__{run_id}"
    out_dir = (out_root or config.RESULTS_DIR / experiment) / trial_id
    cluster = KindCluster(f"{config.CLUSTER_PREFIX}{run_id}")
    trace = Trace()
    record: dict = {
        "schema": SCHEMA, "run_id": run_id, "trial_id": trial_id, "experiment": experiment,
        "trial_index": trial_index,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "outcome": None, "invalid_reason": None,
        "scenario": {"id": scn.id, "revision": scn.revision, "digest": scn.digest, "seed": seed,
                     "parameters": scn.params, "tags": scn.tags,
                     "profiles": {k: {"domain": v.get("domain"), "competency": v.get("primary_competency")}
                                  for k, v in scn.raw["profiles"].items() if v.get("enabled")}},
        "agent": agent.describe(),
        "limits": scn.budgets, "termination": None,
    }
    agent_start = agent_end = None
    try:
        # PROVISION
        try:
            cluster.create()
            record["environment"] = cluster.fingerprint() | {"kops_git_sha": _git_sha()}
        except BackendError as e:
            raise InvalidTrial("provision_failed", str(e))
        # SETUP
        fixtures = config.RUN_DIR / f"{cluster.name}-fixtures"
        fixtures.mkdir(parents=True, exist_ok=True)
        for f in sorted((scn.dir / "fixtures").glob("*")):
            (fixtures / f.name).write_text(scn.text(f"fixtures/{f.name}"))
        env_extra = {f"KOPS_P_{k.upper()}": str(v) for k, v in scn.params.items()}
        env_extra["KOPS_FIXTURES"] = str(fixtures)
        try:
            cluster.run_setup(scn.dir / scn.raw["setup"]["script"], env_extra)
        except (BackendError, subprocess.TimeoutExpired) as e:
            raise InvalidTrial("setup_failed", str(e))
        # READY
        ver = Verifier(cluster, scn.criteria(), scn.raw["verification"].get("settle"))
        try:
            ver.capture_baselines()
        except Exception as e:
            raise InvalidTrial("baseline_failed", str(e))
        record["setup_confirm"] = _confirm_setup(scn, ver)
        baseline_snapshot = cluster.snapshot_namespace(scn.namespace)
        # RUN AGENT
        b = scn.budgets
        gw = Gateway(cluster.agent_kubeconfig, trace, max_steps=b["max_steps"],
                     max_wall_s=b["max_wall_seconds"],
                     per_action_timeout_s=b["per_action_timeout_seconds"],
                     max_output_bytes=b.get("max_output_bytes_per_action", 8192))
        agent_start = time.monotonic()
        try:
            outcome: AgentOutcome = agent.run(scn.agent_view(), gw)
        except ModelError as e:
            raise InvalidTrial("model_api_error", str(e))
        agent_end = time.monotonic()
        record["termination"] = outcome.termination
        record["claim"] = {"submitted": outcome.termination == "submitted", "text": outcome.claim}
        # VERIFY (after the agent session is over)
        results = ver.evaluate()
        record["verifier"] = {"criteria": [asdict(r) for r in results],
                              "required_passed": sum(1 for r in results if r.required and r.status == PASS),
                              "required_total": sum(1 for r in results if r.required)}
        record["outcome"] = Verifier.outcome(results)
        if record["outcome"] == "INVALID":
            bad = [r for r in results if r.status == "error"]
            record["invalid_reason"] = "verifier_error: " + "; ".join(f"{r.id}: {r.evidence}" for r in bad)
        # COLLECT
        final = cluster.snapshot_namespace(scn.namespace)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "final-state.yaml").write_text(final)
        record["state_changed"] = hashlib.sha256(final.encode()).hexdigest() != \
            hashlib.sha256(baseline_snapshot.encode()).hexdigest()
    except InvalidTrial as e:
        record["outcome"], record["invalid_reason"] = "INVALID", f"{e.reason}: {e.detail}"
    except Exception:
        record["outcome"] = "INVALID"
        record["invalid_reason"] = "harness_error: " + traceback.format_exc()[-1500:]
    finally:
        # CLEANUP: the cluster is destroyed, so the next trial can never inherit state.
        try:
            cluster.delete()
            clean = not cluster.container_exists()
        except Exception as e:
            clean = False
            record.setdefault("cleanup_error", str(e))
        record["reset"] = {"strategy": "destroy-cluster", "clean": clean}
        for p in (config.RUN_DIR / f"{cluster.name}-fixtures",):
            if p.exists():
                for f in p.iterdir():
                    f.unlink()
                p.rmdir()
    wall = (agent_end - agent_start) if agent_start and agent_end else 0.0
    record["metrics"] = derive_metrics(trace.events, wall)
    record["failure_labels_auto"] = auto_failure_labels(
        record["outcome"], record["metrics"], record.get("termination") or "")
    record["total_seconds"] = round(time.time() - started, 1)
    write_trial(out_dir, record)
    trace.write(out_dir / "trace.jsonl")
    record["_dir"] = str(out_dir)
    return record
