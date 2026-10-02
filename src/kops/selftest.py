"""kops selftest: a scenario is trusted only if the verifier behaves correctly.

  setup confirm (negative control) -> null agent FAILs -> each wrong-fix FAILs
  -> oracle PASSes N times -> cluster destroyed every time.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .harness import NullAgent, ScriptedAgent
from .runner import run_trial


def selftest(scenario_dir: Path, seed: int = 1, repeats: int = 3, jobs: int = 3,
             out_root: Path | None = None) -> tuple[bool, list[dict]]:
    from .scenario import load_scenario
    scn = load_scenario(scenario_dir, seed)
    plan: list[tuple[str, object, str]] = [("null", NullAgent(), "FAIL")]
    for rel in scn.negative_solutions():
        name = "wrong:" + Path(rel).stem
        plan.append((name, ScriptedAgent(name, scn.reference_commands(rel)), "FAIL"))
    for i in range(repeats):
        plan.append((f"oracle#{i + 1}", ScriptedAgent("oracle", scn.reference_commands()), "PASS"))

    def go(item):
        label, agent, expected = item
        rec = run_trial(scenario_dir, agent, seed=seed, experiment="selftest",
                        trial_index=0, out_root=out_root)
        return {"check": label, "expected": expected, "outcome": rec["outcome"],
                "reason": rec.get("invalid_reason"), "clean_reset": rec["reset"]["clean"],
                "criteria": {c["id"]: c["status"] for c in rec.get("verifier", {}).get("criteria", [])},
                "seconds": rec["total_seconds"]}

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        rows = list(ex.map(go, plan))
    ok = all(r["outcome"] == r["expected"] and r["clean_reset"] for r in rows)
    return ok, rows
