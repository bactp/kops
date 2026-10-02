"""Scenario loading: seeded parameter rendering, content digest, agent view."""
from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_TOKEN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class ScenarioError(Exception):
    pass


def render(text: str, params: dict) -> str:
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in params:
            raise ScenarioError(f"unknown template parameter {key!r}")
        return str(params[key])

    return _TOKEN.sub(sub, text)


def make_params(spec: dict, seed: int) -> dict:
    """Deterministic parameter values from the trial seed."""
    rng = random.Random(seed)
    out: dict = {}
    for name in sorted(spec):
        p = spec[name]
        t = p["type"]
        if t == "dns-label":
            out[name] = f"{p.get('prefix', '')}{rng.getrandbits(16):04x}"
        elif t == "choice":
            out[name] = rng.choice(p["choices"])
        elif t == "port":
            out[name] = rng.randint(p["min"], p["max"])
        else:
            raise ScenarioError(f"unsupported parameter type {t!r}")
    return out


def tree_digest(root: Path) -> str:
    """sha256 over the whole scenario tree, hidden files included."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(str(p.relative_to(root)).encode())
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    return "sha256:" + h.hexdigest()


@dataclass
class Scenario:
    dir: Path
    raw: dict
    seed: int
    params: dict
    digest: str
    tags: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.raw["id"]

    @property
    def revision(self) -> int:
        return self.raw["revision"]

    @property
    def budgets(self) -> dict:
        return self.raw["budgets"]

    @property
    def namespace(self) -> str:
        return self.params["ns"]

    def text(self, relpath: str) -> str:
        return render((self.dir / relpath).read_text(), self.params)

    def agent_view(self) -> str:
        """The only scenario content an agent ever receives."""
        ctx = self.raw["task"].get("agent_context", {})
        ctx = {k: render(str(v), self.params) for k, v in ctx.items()}
        lines = [self.text(self.raw["task"]["statement_file"]).strip(), ""]
        lines += [f"{k}: {v}" for k, v in ctx.items()]
        return "\n".join(lines)

    def criteria(self) -> list[dict]:
        doc = yaml.safe_load(self.text(self.raw["verification"]["criteria_file"]))
        return doc["criteria"]

    def setup_confirm(self) -> dict:
        return self.raw["setup"]["confirm"]

    def reference_commands(self, relpath: str | None = None) -> list[str]:
        """One kubectl command per line; '#' lines and blanks ignored."""
        rel = relpath or self.raw["reference"]["solution"]
        out = []
        for line in self.text(rel).splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
        return out

    def negative_solutions(self) -> list[str]:
        return list(self.raw["reference"].get("negative_solutions", []))


def load_scenario(path: Path, seed: int = 1) -> Scenario:
    path = Path(path)
    # scenario.yaml has no template tokens outside `task.parameters` values,
    # but initial_state text does; render after reading parameters.
    raw_text = (path / "scenario.yaml").read_text()
    pre = yaml.safe_load(_TOKEN.sub("X", raw_text))
    params = make_params(pre["task"]["parameters"], seed)
    raw = yaml.safe_load(render(raw_text, params))
    return Scenario(
        dir=path, raw=raw, seed=seed, params=params,
        digest=tree_digest(path), tags=raw.get("tags", []),
    )
