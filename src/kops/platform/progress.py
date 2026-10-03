"""Per-(user, scenario) progress: status rules from docs/platform-api.md."""
from __future__ import annotations

from sqlalchemy import select

from .catalog import Catalog
from .db import Database, ProgressRow, iso, utcnow

_RANK = {None: 0, "INVALID": 1, "FAIL": 2, "PASS": 3}


def status_of(p: ProgressRow | None) -> str:
    if p is None:
        return "none"
    if p.solved_clean:
        return "solved"
    if p.solved_assisted:
        return "solved_assisted"
    return "attempted" if p.checks > 0 else "none"


def _row(s, user_id: str, scenario_id: str) -> ProgressRow:
    p = s.get(ProgressRow, (user_id, scenario_id))
    if p is None:
        p = ProgressRow(user_id=user_id, scenario_id=scenario_id)
        s.add(p)
    return p


def record_attempt(db: Database, user_id: str, scenario_id: str) -> None:
    with db.session() as s:
        p = _row(s, user_id, scenario_id)
        p.attempts = (p.attempts or 0) + 1
        s.commit()


def record_check(db: Database, user_id: str, scenario_id: str, outcome: str, solution_viewed: bool,
                 seconds_delta: int) -> None:
    with db.session() as s:
        p = _row(s, user_id, scenario_id)
        p.checks = (p.checks or 0) + 1
        p.last_checked_at = utcnow()
        p.seconds_spent = (p.seconds_spent or 0) + max(0, seconds_delta)
        if _RANK[outcome] > _RANK[p.best_outcome]:
            p.best_outcome = outcome
        if outcome == "PASS":
            if solution_viewed:
                p.solved_assisted = True
            else:
                p.solved_clean = True
        s.commit()


def record_finish(db: Database, user_id: str, scenario_id: str, solution_viewed: bool,
                  seconds_delta: int) -> None:
    """An attempt ended (next, restart, delete, expiry)."""
    with db.session() as s:
        p = _row(s, user_id, scenario_id)
        p.seconds_spent = (p.seconds_spent or 0) + max(0, seconds_delta)
        if solution_viewed:
            p.solved_assisted = True
        s.commit()


def statuses(db: Database, user_id: str) -> dict[str, str]:
    with db.session() as s:
        rows = s.scalars(select(ProgressRow).where(ProgressRow.user_id == user_id)).all()
    return {r.scenario_id: status_of(r) for r in rows}


def report(db: Database, catalog: Catalog, user_id: str) -> dict:
    with db.session() as s:
        rows = s.scalars(select(ProgressRow).where(ProgressRow.user_id == user_id)).all()
    items, st = [], {}
    for r in rows:
        status = status_of(r)
        st[r.scenario_id] = status
        if status != "none":
            items.append({"scenario_id": r.scenario_id, "status": status, "attempts": r.attempts,
                          "best_outcome": r.best_outcome, "last_checked_at": iso(r.last_checked_at),
                          "seconds_spent": r.seconds_spent})
    summary: dict[str, dict] = {"cka": {}, "ckad": {}}
    for e in catalog.entries.values():
        for prof, meta in e.profiles.items():
            d = summary.setdefault(prof, {}).setdefault(
                meta.get("domain") or "unknown", {"solved": 0, "assisted": 0, "attempted": 0, "total": 0})
            d["total"] += 1
            status = st.get(e.id, "none")
            if status == "solved":
                d["solved"] += 1
            elif status == "solved_assisted":
                d["assisted"] += 1
            elif status == "attempted":
                d["attempted"] += 1
    return {"scenarios": sorted(items, key=lambda i: i["scenario_id"]), "summary": summary}
