"""Experiments: agents x scenarios x seeds x trials, as data. Plus the comparison table."""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from . import config
from .harness import NullAgent, ScriptedAgent, ShellLoopAgent
from .models import OpenAICompatModel
from .runner import run_trial
from .scenario import load_scenario


def build_agent(spec: dict, scn):
    kind = spec["kind"]
    if kind == "noop":
        return NullAgent()
    if kind == "oracle":
        return ScriptedAgent(spec.get("name", "oracle"), scn.reference_commands())
    if kind == "model":
        m = spec["model"]
        model = OpenAICompatModel(m["id"], m["base_url"], m.get("api_key_env"),
                                  temperature=m.get("temperature", 0.0),
                                  max_tokens=m.get("max_tokens", 1024), seed=m.get("seed"))
        return ShellLoopAgent(spec["name"], model)
    raise ValueError(f"unknown agent kind {kind!r}")


def run_experiment(path: Path, jobs: int = 2) -> Path:
    exp = yaml.safe_load(Path(path).read_text())
    name = exp["name"]
    out_root = config.RESULTS_DIR / name
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "experiment.yaml").write_text(Path(path).read_text())
    work = []
    for sc in exp["scenarios"]:
        sdir = config.SCENARIOS_DIR / sc
        for seed in exp.get("seeds", [1]):
            scn = load_scenario(sdir, seed)
            for spec in exp["agents"]:
                for t in range(exp.get("trials", 1)):
                    work.append((sdir, build_agent(spec, scn), seed, t))

    def go(w):
        sdir, agent, seed, t = w
        r = run_trial(sdir, agent, seed=seed, experiment=name, trial_index=t, out_root=out_root)
        print(f"{r['trial_id']}: {r['outcome']}  ({r['total_seconds']}s)", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        list(ex.map(go, work))
    return out_root


def compare(exp_dir: Path) -> str:
    rows: dict[str, list[dict]] = {}
    for f in sorted(Path(exp_dir).glob("*/trial.json")):
        t = json.loads(f.read_text())
        rows.setdefault(t["agent"]["name"], []).append(t)
    hdr = ("agent", "n", "PASS", "FAIL", "INVALID", "pass_rate", "exec_cmd_rate", "invalid_act",
           "recovery", "steps", "wall_s")
    lines = ["  ".join(f"{h:>13}" if i else f"{h:<22}" for i, h in enumerate(hdr))]
    mean = lambda xs: (sum(xs) / len(xs)) if xs else float("nan")
    for agent, ts in rows.items():
        scored = [t for t in ts if t["outcome"] in ("PASS", "FAIL")]
        n_pass = sum(t["outcome"] == "PASS" for t in ts)
        cells = [agent, len(ts), n_pass, sum(t["outcome"] == "FAIL" for t in ts),
                 sum(t["outcome"] == "INVALID" for t in ts),
                 f"{n_pass / len(scored):.2f}" if scored else "-",
                 f"{mean([t['metrics']['executable_command_rate'] for t in scored if t['metrics']['executable_command_rate'] is not None]):.2f}",
                 f"{mean([t['metrics']['invalid_actions'] for t in scored]):.1f}",
                 f"{mean([t['metrics']['recovery_count'] for t in scored]):.1f}",
                 f"{mean([t['metrics']['steps'] for t in scored]):.1f}",
                 f"{mean([t['metrics']['wall_seconds'] for t in scored]):.0f}"]
        lines.append("  ".join(f"{str(c):>13}" if i else f"{str(c):<22}" for i, c in enumerate(cells)))
    lines.append("\npass_rate is over scored trials (PASS+FAIL); INVALID trials are reported, never counted as FAIL.")
    return "\n".join(lines)
