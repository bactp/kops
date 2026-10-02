"""Minimal lint: render with several seeds, validate against the JSON Schemas, check cross-file rules."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

from . import config
from .scenario import load_scenario

SCHEMAS = config.ROOT / "schemas"


def _validator(name: str):
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text())
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def lint_scenario(path: Path, seeds=(1, 2, 3)) -> list[str]:
    problems: list[str] = []
    sv, cv, pv = _validator("scenario"), _validator("criteria"), _validator("provenance")
    for seed in seeds:
        scn = load_scenario(path, seed)
        for e in sv.iter_errors(scn.raw):
            problems.append(f"seed {seed} scenario.yaml: {e.message[:160]}")
        crit_doc = yaml.safe_load(scn.text(scn.raw["verification"]["criteria_file"]))
        for e in cv.iter_errors(crit_doc):
            problems.append(f"seed {seed} criteria.yaml: {e.message[:160]}")
        prov = yaml.safe_load(scn.text(scn.raw["metadata"]["provenance"]["file"]))
        for e in pv.iter_errors(prov):
            problems.append(f"seed {seed} provenance.yaml: {e.message[:160]}")
        inv = {i["id"] for i in scn.raw["expected_invariants"]}
        crit_inv = {c["invariant"] for c in crit_doc["criteria"]}
        if inv != crit_inv:
            problems.append(f"invariants without criteria / orphans: {sorted(inv ^ crit_inv)}")
        conf = scn.setup_confirm()
        for i in conf["must_fail"] + conf.get("must_pass", []):
            if i not in inv:
                problems.append(f"setup.confirm references unknown invariant {i}")
        for rel in [scn.raw["task"]["statement_file"], scn.raw["setup"]["script"],
                    scn.raw["reference"]["solution"], *scn.negative_solutions()]:
            if not (path / rel).exists():
                problems.append(f"missing file {rel}")
        if scn.raw["backend"]["class"] != "kind":
            problems.append("only backend.class=kind is implemented")
    return sorted(set(problems))
