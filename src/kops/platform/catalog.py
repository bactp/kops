"""Scenario catalogue: metadata read from scenarios/*/scenario.yaml, plus provider availability."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..reset import declared_reset
from ..scenario import ScenarioError, render

log = logging.getLogger("kops.catalog")
_TOKEN = re.compile(r"\{\{\s*\w+\s*\}\}")
NOT_VALIDATED = "not yet validated on this provider"
GENERIC_EXPLANATION = "No written explanation is available for this task yet."


@dataclass
class Entry:
    id: str
    title: str
    difficulty: int
    tags: list[str]
    profiles: dict[str, dict]
    reset: str
    dir: Path
    hint_count: int = 0
    available: bool = True
    note: str | None = None

    def public(self) -> dict:
        return {"id": self.id, "title": self.title, "difficulty": self.difficulty, "tags": self.tags,
                "profiles": self.profiles, "available": self.available,
                "availability_note": self.note, "reset": self.reset}


def parse_hints(text: str) -> list[str]:
    """Numbered list ('1. text', continuation lines allowed) -> list of hint texts."""
    hints: list[str] = []
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)[.)]\s+(.*)", line)
        if m:
            hints.append(m.group(2).strip())
        elif hints and line.strip() and not line.startswith("#"):
            hints[-1] += "\n" + line.strip()
    return hints


def read_available(path: Path | None) -> set[str] | None:
    """Ids listed in the file; None means everything ('*'). A missing file lists nothing."""
    if path is None or not path.exists():
        return set()
    ids = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            if line == "*":
                return None
            ids.add(line)
    return ids


@dataclass
class Catalog:
    scenarios_dir: Path
    available_file: Path | None = None      # None: every scenario is available
    entries: dict[str, Entry] = field(default_factory=dict)

    def load(self) -> "Catalog":
        self.entries = {}
        avail = read_available(self.available_file) if self.available_file else None
        # scenarios whose API-level reset was proven by `kops selftest-vm` (catalog/reset-api.txt, next to available.txt)
        api_ok = read_available(self.available_file.with_name("reset-api.txt")) if self.available_file and \
            self.available_file.with_name("reset-api.txt").exists() else set()
        for yml in sorted(self.scenarios_dir.glob("*/scenario.yaml")):
            try:
                raw = yaml.safe_load(_TOKEN.sub("X", yml.read_text()))
                d = yml.parent
                profiles = {k: {"domain": v.get("domain"), "competency": v.get("primary_competency")}
                            for k, v in raw.get("profiles", {}).items() if v.get("enabled")}
                hints = d / "reference" / "hints.md"
                e = Entry(raw["id"], raw["title"], int(raw["difficulty"]["level"]), list(raw.get("tags", [])),
                          profiles, declared_reset(raw), d,
                          len(parse_hints(hints.read_text())) if hints.exists() else 0)
            except Exception as ex:   # a half-written scenario must not take the platform down
                log.warning("skipping %s: %s", yml.parent.name, ex)
                continue
            if e.reset == "vm" and api_ok and e.id in api_ok:
                e.reset = "api"
            if avail is not None and e.id not in avail:
                e.available, e.note = False, NOT_VALIDATED
            self.entries[e.id] = e
        return self

    def get(self, sid: str) -> Entry | None:
        return self.entries.get(sid)

    def search(self, profile=None, domain=None, difficulty=None, q=None) -> list[Entry]:
        out = []
        for e in self.entries.values():
            profs = [profile] if profile else list(e.profiles)
            if profile and profile not in e.profiles:
                continue
            if domain and not any(e.profiles.get(p, {}).get("domain") == domain for p in profs):
                continue
            if difficulty and e.difficulty != difficulty:
                continue
            if q and q.lower() not in " ".join([e.id, e.title, *e.tags]).lower():
                continue
            out.append(e)
        return out

    # -- content that only the explicit endpoints expose ------------------------------------
    def hints(self, e: Entry, params: dict) -> list[str]:
        p = e.dir / "reference" / "hints.md"
        if not p.exists():
            return []
        return [_render(h, params) for h in parse_hints(p.read_text())]

    def explanation(self, e: Entry, params: dict) -> str:
        p = e.dir / "reference" / "explanation.md"
        return _render(p.read_text(), params) if p.exists() else GENERIC_EXPLANATION


def _render(text: str, params: dict) -> str:
    try:
        return render(text, params)
    except ScenarioError:
        return text
