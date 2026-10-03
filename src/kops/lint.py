"""Minimal lint: render with several seeds, validate against the JSON Schemas, check cross-file rules."""
from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import jsonschema
import yaml

from . import config
from .gateway import FORBIDDEN_FLAGS, SHELL_TOKENS
from .scenario import ScenarioError, load_scenario

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
    problems += lint_content(path, seeds)
    return sorted(set(problems))


def _denylist_rules() -> list[dict]:
    p = config.ROOT / "docs" / "contamination-denylist.yaml"
    if not p.exists():
        return []
    return [r for r in yaml.safe_load(p.read_text()).get("rules", []) if r.get("action") == "fail"]


def _denylist_hits(text: str, rules: list[dict]) -> list[str]:
    """Literal and context matches of the `fail` rules of docs/contamination-denylist.yaml."""
    hits = []
    for r in rules:
        for tok in r.get("tokens", []):
            if r["match"] == "literal":
                found = tok in text
            elif r["match"] == "namespace-context":
                found = re.search(rf"(namespace:\s*|-n\s+|--namespace[= ]|ns/){re.escape(tok)}\b", text) is not None
            elif r["match"] == "resource-name-context":
                found = re.search(rf"(name:\s*|kubectl \w+ \w+ ){re.escape(tok)}\b", text) is not None
            else:
                continue   # `regex` rules need reviewer judgement (see the denylist header)
            if found:
                hits.append(f"{r['id']}:{tok}")
    return hits


def lint_content(path: Path, seeds=(1, 2, 3)) -> list[str]:
    """Rendering and executability checks that JSON Schema cannot express.

    - every template token resolves, and fixtures are valid YAML for every seed;
    - reference solution / wrong-fix lines are single plain kubectl commands that the gateway accepts
      (no shell tokens, no forbidden flags);
    - no `fail` token of the contamination denylist appears in any scenario file.
    """
    problems: list[str] = []
    rules = _denylist_rules()
    for seed in seeds:
        scn = load_scenario(path, seed)
        for f in sorted((path / "fixtures").glob("*")):
            try:
                list(yaml.safe_load_all(scn.text(f"fixtures/{f.name}")))
            except yaml.YAMLError as e:
                problems.append(f"seed {seed} fixtures/{f.name}: invalid YAML after rendering: {str(e)[:100]}")
            except ScenarioError as e:
                problems.append(f"seed {seed} fixtures/{f.name}: {e}")
        try:
            scn.text(scn.raw["setup"]["script"])
        except ScenarioError as e:
            problems.append(f"seed {seed} setup script: {e}")
        for rel in [scn.raw["reference"]["solution"], *scn.negative_solutions()]:
            try:
                cmds = scn.reference_commands(rel)
            except ScenarioError as e:
                problems.append(f"seed {seed} {rel}: {e}")
                continue
            for cmd in cmds:
                try:
                    argv = shlex.split(cmd)
                except ValueError as e:
                    problems.append(f"seed {seed} {rel}: unparsable command {cmd[:60]!r}: {e}")
                    continue
                if not argv or argv[0] != "kubectl":
                    problems.append(f"seed {seed} {rel}: not a kubectl command: {cmd[:60]!r}")
                elif any(a in SHELL_TOKENS for a in argv):
                    problems.append(f"seed {seed} {rel}: shell syntax in {cmd[:60]!r}")
                elif any(a == f or a.startswith(f + "=") for a in argv for f in FORBIDDEN_FLAGS):
                    problems.append(f"seed {seed} {rel}: forbidden flag in {cmd[:60]!r}")
    for f in sorted(path.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts:
            for h in _denylist_hits(f.read_text(errors="ignore"), rules):
                problems.append(f"contamination denylist hit in {f.relative_to(path)}: {h}")
    return sorted(set(problems))
