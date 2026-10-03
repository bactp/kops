"""Interactive lab: you play the candidate. up -> work with kubectl -> verify -> down."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from . import config
from .backend_kind import KindCluster
from .runner import InvalidTrial, _confirm_setup
from .scenario import load_scenario
from .verifier import Verifier


def _state_path(scenario_id: str) -> Path:
    return config.RUN_DIR / f"lab-{scenario_id}.json"


def up(scenario_dir: Path, seed: int = 1) -> str:
    scn = load_scenario(scenario_dir, seed)
    sp = _state_path(scn.id)
    if sp.exists():
        raise SystemExit(f"A lab for {scn.id} already exists. Run `kops lab down {scn.id}` first.")
    cluster = KindCluster(f"{config.CLUSTER_PREFIX}lab{uuid.uuid4().hex[:4]}",
                          workers=scn.raw["backend"]["topology"]["workers"])
    try:
        cluster.create()
        fixtures = config.RUN_DIR / f"{cluster.name}-fixtures"
        fixtures.mkdir(parents=True, exist_ok=True)
        for f in sorted((scn.dir / "fixtures").glob("*")):
            (fixtures / f.name).write_text(scn.text(f"fixtures/{f.name}"))
        env = {f"KOPS_P_{k.upper()}": str(v) for k, v in scn.params.items()} | {"KOPS_FIXTURES": str(fixtures)}
        cluster.run_setup(scn.dir / scn.raw["setup"]["script"], env)
        ver = Verifier(cluster, scn.criteria(), scn.raw["verification"].get("settle"))
        ver.capture_baselines()
        _confirm_setup(scn, ver)
    except BaseException:
        cluster.delete()
        raise
    baselines = {k[1]: v for k, v in ver.ctx.items() if isinstance(k, tuple)}
    task_file = config.RUN_DIR / f"lab-{scn.id}.task.md"
    task_file.write_text(scn.agent_view() + "\n")
    sp.write_text(json.dumps({"cluster": cluster.name, "seed": seed, "scenario": str(scn.dir),
                              "baselines": baselines, "started": time.time()}))
    path = f"{config.BIN_DIR}:$PATH"
    return (f"\n=== TASK ===\n{scn.agent_view()}\n\n=== LAB READY (cluster {cluster.name}) ===\n"
            f"Work in your shell with:\n  export PATH={path}\n"
            f"  export KUBECONFIG={cluster.agent_kubeconfig}\n"
            f"Show the task again:  kops lab task {scn.id}\n"
            f"When done:  kops lab verify {scn.id}   (add --wait to give the cluster up to 60 s to settle)\n"
            f"To remove:  kops lab down {scn.id}\n")


def _attach(scenario_dir: Path):
    scn = None
    for sp in config.RUN_DIR.glob("lab-*.json"):
        st = json.loads(sp.read_text())
        if Path(st["scenario"]).name == scenario_dir.name:
            scn = load_scenario(Path(st["scenario"]), st["seed"])
            cluster = KindCluster(st["cluster"])
            cluster.created = True
            return scn, cluster, st, sp
    raise SystemExit(f"No running lab for {scenario_dir.name}. Run `kops lab up` first.")


def verify(scenario_dir: Path, wait: bool = False) -> int:
    scn, cluster, st, _ = _attach(scenario_dir)
    ver = Verifier(cluster, scn.criteria(), scn.raw["verification"].get("settle"))
    for cid, digest in st["baselines"].items():
        ver.ctx[("baseline", cid)] = digest
    # A human can simply re-run verify, so do not wait for convergence unless asked.
    results = ver.evaluate(settle=wait)
    for r in results:
        print(f"[{r.status.upper():5}] {r.id:<24} {'(required)' if r.required else ''}  {r.evidence}")
    outcome = Verifier.outcome(results)
    print(f"\nRESULT: {outcome}")
    return 0 if outcome == "PASS" else 1


def task(scenario_dir: Path) -> str:
    scn, _, _, _ = _attach(scenario_dir)
    return scn.agent_view()


def down(scenario_dir: Path) -> None:
    _, cluster, _, sp = _attach(scenario_dir)
    cluster.delete()
    sp.unlink(missing_ok=True)
    print("lab removed; cluster destroyed:", not cluster.container_exists())
