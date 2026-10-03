"""selftest on a provider sandbox (KubeVirt): the same proof as `kops selftest`, but one sandbox is reused for many
scenarios and returned to its initial state by the API-level reset between trials.

For every scenario: the setup confirm (negative control) must hold, the null agent must FAIL, every wrong-fix must
FAIL and the reference solution must PASS (twice). After each trial the cluster is reset and the state digest must
equal the baseline; a scenario whose reset never reaches the baseline needs `reset: vm`.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import time
import traceback
import uuid
from pathlib import Path

from .gateway import BudgetExhausted, Gateway, Trace
from .providers.base import SandboxProvider, SandboxSpec
from .reset import Reset
from .runner import InvalidTrial, _confirm_setup
from .scenario import Scenario, load_scenario
from .verifier import Verifier


def _prepare(sb, scn: Scenario) -> Verifier:
    tmp = Path(tempfile.mkdtemp(prefix="kops-fixtures-"))
    try:
        for f in sorted((scn.dir / "fixtures").glob("*")):
            (tmp / f.name).write_text(scn.text(f"fixtures/{f.name}"))
        env = {f"KOPS_P_{k.upper()}": str(v) for k, v in scn.params.items()} | {"KOPS_FIXTURES": str(tmp)}
        sb.run_setup(scn.dir / scn.raw["setup"]["script"], env)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ver = Verifier(sb, scn.criteria(), scn.raw["verification"].get("settle"))
    ver.capture_baselines()
    _confirm_setup(scn, ver)
    return ver


def _apply(sb, scn: Scenario, commands: list[str]) -> None:
    gw = Gateway(sb.admin_kubeconfig, Trace(), max_steps=100, max_wall_s=300, per_action_timeout_s=60)
    try:
        for c in commands:
            gw.run(c)
    except BudgetExhausted:
        pass


def run_one(sb, scenario_dir: Path, seed: int = 1, repeats: int = 2, log=print) -> dict:
    scn = load_scenario(scenario_dir, seed)
    res = {"id": scn.id, "ok": False, "reset_api_ok": True, "trials": [], "seconds": 0.0, "error": None}
    t0 = time.time()
    reset = Reset(sb)
    pristine = reset.capture_baseline()
    trials = [("null", [], "FAIL")]
    trials += [(f"wrong:{Path(r).stem}", scn.reference_commands(r), "FAIL") for r in scn.negative_solutions()]
    trials += [(f"oracle#{i + 1}", scn.reference_commands(), "PASS") for i in range(repeats)]
    try:
        for label, cmds, want in trials:
            t1 = time.time()
            ver = _prepare(sb, scn)
            _apply(sb, scn, cmds)
            outcome = Verifier.outcome(ver.evaluate())
            restored = reset.wait_restored(pristine, timeout=150, interval=3)
            res["trials"].append({"trial": label, "expected": want, "got": outcome, "reset_restored": restored,
                                  "seconds": round(time.time() - t1, 1)})
            log(f"   {scn.id} {label:<34} expected={want:<4} got={outcome:<7} reset_restored={restored} {time.time() - t1:.0f}s")
            res["reset_api_ok"] &= restored
            if not restored:                                 # leave the sandbox clean for the next trial
                res["error"] = "API reset did not restore the baseline"
                return _finish(res, t0)
        res["ok"] = all(t["got"] == t["expected"] for t in res["trials"])
    except InvalidTrial as e:
        res["error"] = f"INVALID: {e.reason}: {e.detail}"[:300]
    except Exception as e:
        res["error"] = f"{type(e).__name__}: {e}"[:300] + " | " + traceback.format_exc()[-300:]
    return _finish(res, t0)


def _finish(res: dict, t0: float) -> dict:
    res["seconds"] = round(time.time() - t0, 1)
    return res


def selftest_group(provider: SandboxProvider, scenario_dirs: list[Path], workers: int, log=print) -> list[dict]:
    sid = "st_" + uuid.uuid4().hex[:8]
    log(f"== sandbox {sid}: {len(scenario_dirs)} scenario(s), workers={workers}")
    sb = provider.provision(SandboxSpec(session_id=sid, owner="selftest", workers=workers, labels={"kops.io/exempt": "true"}), log)
    out = []
    try:
        for d in scenario_dirs:
            r = run_one(sb, d, log=log)
            out.append(r)
            if r["error"] and "reset" in r["error"]:
                log("   reset failed: recreating the sandbox")
                sb = provider.recreate(sb, log)
    finally:
        provider.destroy(sb.id)
    return out


def summarize(results: list[dict]) -> dict:
    return {"passed": [r["id"] for r in results if r["ok"]],
            "failed": {r["id"]: (r["error"] or [t for t in r["trials"] if t["got"] != t["expected"]]) for r in results if not r["ok"]},
            "reset_api": [r["id"] for r in results if r["ok"] and r["reset_api_ok"]],
            "reset_vm": [r["id"] for r in results if r["ok"] and not r["reset_api_ok"]]}


def main(argv=None) -> int:
    import argparse
    from . import config
    ap = argparse.ArgumentParser(prog="kops selftest-vm")
    ap.add_argument("scenarios", nargs="*", help="scenario ids (default: all with the same worker count)")
    ap.add_argument("--workers", type=int, default=0, help="only scenarios with this many extra workers")
    ap.add_argument("--out", default="/tmp/selftest-vm.json")
    ap.add_argument("--provider", default="kubevirt")
    ap.add_argument("--shard", default="1/1", help="i/n: take every n-th scenario starting at i (parallel jobs)")
    a = ap.parse_args(argv)
    ids = a.scenarios or sorted(p.name for p in config.SCENARIOS_DIR.iterdir() if (p / "scenario.yaml").exists())
    si, sn = (int(x) for x in a.shard.split("/"))
    ids = ids[si - 1::sn]
    dirs = []
    for i in ids:
        d = config.SCENARIOS_DIR / i
        if load_scenario(d, 1).raw["backend"]["topology"]["workers"] == a.workers:
            dirs.append(d)
    if a.provider == "kubevirt":
        from .providers.kubevirt import KubeVirtProvider
        provider = KubeVirtProvider()
    elif a.provider == "kind":
        from .providers.kind import KindProvider
        provider = KindProvider(max_sessions=2)
    else:
        raise SystemExit(f"unknown provider {a.provider!r}")
    results = selftest_group(provider, dirs, a.workers, log=lambda m: print(m, flush=True))
    summ = summarize(results)
    Path(a.out).write_text(json.dumps({"summary": summ, "results": results}, indent=1))
    print("SUMMARY " + json.dumps(summ), flush=True)
    print("COUNTS " + json.dumps({k: len(v) for k, v in summ.items()}), flush=True)
    return 0 if not summ["failed"] else 1
