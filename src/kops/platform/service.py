"""Session service: lifecycle, quota, capacity, check, hints, reset, expiry, sweeper."""
from __future__ import annotations

import json
import logging
import random
import secrets
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

from sqlalchemy import func, select, update

from ..providers.base import SandboxSpec
from ..reset import Baseline, Reset
from ..runner import InvalidTrial, _confirm_setup
from ..scenario import Scenario, load_scenario
from ..verifier import Verifier
from . import progress as prog
from .catalog import Catalog, Entry
from .db import CheckRow, Database, SessionEvent, SessionRow, User, iso, utcnow
from .errors import ApiError
from .settings import Settings

log = logging.getLogger("kops.service")

TERMINAL = {"ENDED", "DESTROYED", "INVALID"}      # no longer counts against the quota
GONE = {"ENDED", "DESTROYED"}
OPEN = {"ACTIVE", "CHECKING"}


def _default_verifier(sandbox, criteria, settle):
    return Verifier(sandbox, criteria, settle)


class SessionService:
    def __init__(self, settings: Settings, db: Database, provider, catalog: Catalog,
                 verifier_factory=_default_verifier):
        self.cfg, self.db, self.provider, self.catalog = settings, db, provider, catalog
        self.verifier_factory = verifier_factory
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="kops-bg")
        self._sandboxes: dict = {}
        self._lock = threading.Lock()
        self._destroying: set[str] = set()
        self._scn_cache: dict[tuple, Scenario] = {}

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    # -- small DB helpers ------------------------------------------------------------------
    def _row(self, s, sid: str) -> SessionRow:
        row = s.get(SessionRow, sid)
        if row is None:
            raise ApiError("not_found", "no such session")
        return row

    def update(self, sid: str, **fields) -> None:
        with self.db.session() as s:
            row = self._row(s, sid)
            for k, v in fields.items():
                setattr(row, k, v)
            row.rev += 1
            s.commit()

    def transition(self, sid: str, state: str, message: str | None = None, *, only_from=None) -> bool:
        """Change state unless the session was already ended; False if refused."""
        with self.db.session() as s:
            row = self._row(s, sid)
            if row.state in GONE and state != "DESTROYED":
                return False
            if only_from and row.state not in only_from:
                return False
            row.state, row.message = state, message
            row.rev += 1
            s.commit()
        return True

    def log(self, sid: str, line: str) -> None:
        with self.db.session() as s:
            s.add(SessionEvent(session_id=sid, line=line[:2000]))
            s.commit()

    def state_of(self, sid: str) -> str | None:
        with self.db.session() as s:
            row = s.get(SessionRow, sid)
            return row.state if row else None

    def scenario(self, entry: Entry, seed: int) -> Scenario:
        key = (entry.id, seed)
        if key not in self._scn_cache:
            if len(self._scn_cache) > 256:
                self._scn_cache.clear()
            self._scn_cache[key] = load_scenario(entry.dir, seed)
        return self._scn_cache[key]

    # -- views -----------------------------------------------------------------------------
    def to_json(self, row: SessionRow, owner: str) -> dict:
        task = None
        entry = self.catalog.get(row.scenario_id) if row.scenario_id else None
        if row.type == "practice" and entry:
            scn = self.scenario(entry, row.seed or 1)
            prof = "cka" if "cka" in entry.profiles else next(iter(entry.profiles), None)
            task = {"title": scn.raw["title"], "text_md": scn.text(scn.raw["task"]["statement_file"]),
                    "domain": entry.profiles.get(prof, {}).get("domain") if prof else None,
                    "difficulty": entry.difficulty}
        sb = self._sandboxes.get(row.id)
        targets = [{"name": t.name, "role": t.role} for t in sb.targets()] if sb and row.state in (
            OPEN | {"RESETTING", "SETUP", "CONFIRMING"}) else []
        return {"id": row.id, "type": row.type, "state": row.state, "owner": owner,
                "created_at": iso(row.created_at), "expires_at": iso(row.expires_at),
                "extensions": row.extensions, "scenario_id": row.scenario_id, "task": task,
                "targets": targets, "hints_used": len(json.loads(row.hints_read_json)),
                "solution_viewed": row.solution_viewed, "attempt": row.attempt,
                "last_check": json.loads(row.last_check_json) if row.last_check_json else None,
                "reset": row.reset_mode, "message": row.message}

    def get(self, user: User, sid: str) -> SessionRow:
        with self.db.session() as s:
            row = s.get(SessionRow, sid)
        if row is None or (row.user_id != user.id and not user.is_admin):
            raise ApiError("not_found", "no such session")
        return row

    def view(self, user: User, sid: str) -> dict:
        row = self.get(user, sid)
        return self.to_json(row, self._username(row.user_id))

    def _username(self, user_id: str) -> str:
        with self.db.session() as s:
            u = s.get(User, user_id)
            return u.username if u else "?"

    def list_for(self, user: User, all_users: bool = False) -> list[dict]:
        with self.db.session() as s:
            q = select(SessionRow, User.username).join(User, User.id == SessionRow.user_id)
            if not all_users:
                q = q.where(SessionRow.user_id == user.id)
            rows = s.execute(q).all()
        rows.sort(key=lambda r: (r[0].state in TERMINAL, -r[0].created_at.timestamp()))
        return [self.to_json(r, name) for r, name in rows]

    # -- create ----------------------------------------------------------------------------
    def _capacity(self):
        try:
            cap = self.provider.capacity()
        except Exception as e:
            raise ApiError("provider_error", f"capacity query failed: {e}")
        limits = [x for x in (cap.max_sessions, self.cfg.max_sessions) if x and x > 0]
        with self.db.session() as s:
            mine = s.scalar(select(func.count()).select_from(SessionRow).where(
                SessionRow.state.not_in(TERMINAL))) or 0
        return cap, (min(limits) if limits else 10 ** 9), max(cap.active_sessions, mine)

    def create(self, user: User, typ: str, scenario_id: str | None, seed: int | None) -> dict:
        entry = None
        if typ == "practice":
            entry = self.catalog.get(scenario_id or "")
            if entry is None:
                raise ApiError("invalid_request", f"unknown scenario {scenario_id!r}")
            if not entry.available:
                raise ApiError("invalid_request", f"scenario not available: {entry.note}")
        elif typ == "playground":
            if not self.cfg.features.get("playground", True):
                raise ApiError("invalid_request", "playground is disabled")
        else:
            raise ApiError("invalid_request", "type must be practice or playground")
        with self._lock:
            with self.db.session() as s:
                n = s.scalar(select(func.count()).select_from(SessionRow).where(
                    SessionRow.user_id == user.id, SessionRow.state.not_in(TERMINAL))) or 0
            if n >= self.cfg.sessions_per_user:
                raise ApiError("quota_exceeded", "you already have an active session")
            _, maxs, active = self._capacity()
            if active >= maxs:
                raise ApiError("capacity_exceeded", "no capacity right now, try again later")
            sid = "s_" + secrets.token_hex(4)
            ttl = self.cfg.practice_ttl_minutes if typ == "practice" else self.cfg.playground_ttl_minutes
            row = SessionRow(id=sid, user_id=user.id, type=typ, state="REQUESTED",
                             expires_at=utcnow() + timedelta(minutes=ttl))
            if entry:
                seed = int(seed) if seed is not None else random.randrange(1, 2 ** 31)
                scn = self.scenario(entry, seed)
                row.scenario_id, row.seed, row.params_json = entry.id, seed, json.dumps(scn.params)
                row.reset_mode = entry.reset
                row.workers = scn.raw["backend"]["topology"]["workers"]
            else:
                row.workers = 1
            with self.db.session() as s:
                s.add(row)
                s.commit()
        self._pool.submit(self._provision_flow, sid, user.username)
        return self.to_json(row, user.username)

    # -- background flows ------------------------------------------------------------------
    def _provision_flow(self, sid: str, owner: str) -> None:
        try:
            if not self.transition(sid, "PROVISIONING", only_from={"REQUESTED"}):
                return
            with self.db.session() as s:
                row = self._row(s, sid)
                spec = SandboxSpec(session_id=sid, owner=owner, workers=row.workers,
                                   ttl_seconds=int((row.expires_at - utcnow()).total_seconds()),
                                   labels={"kops-session": sid, "kops-owner": owner})
                typ, entry = row.type, self.catalog.get(row.scenario_id or "")
            self.log(sid, "provisioning sandbox")
            sb = self.provider.provision(spec, lambda line: self.log(sid, line))
            self._sandboxes[sid] = sb
            self.update(sid, sandbox_id=sb.id)
            if self.state_of(sid) in GONE:
                self._destroy(sid)
                return
            if typ == "playground":
                self.update(sid, attempt=1)
                self.transition(sid, "ACTIVE")
                self.log(sid, "playground ready")
                return
            self.update(sid, attempt=1)
            self._setup_flow(sid, entry)
        except Exception as e:
            self._invalid(sid, f"provisioning failed: {_short(e)}")

    def _setup_flow(self, sid: str, entry: Entry) -> None:
        """SETUP -> CONFIRMING -> ACTIVE for the scenario currently stored on the session."""
        tmp = None
        try:
            with self.db.session() as s:
                row = self._row(s, sid)
                seed, user_id, pristine = row.seed or 1, row.user_id, row.pristine_json
            sb = self._sandboxes[sid]
            scn = self.scenario(entry, seed)
            if entry.reset == "api" and not pristine:
                self.log(sid, "capturing cluster baseline")
                self.update(sid, pristine_json=Reset(sb).capture_baseline().to_json())
            if not self.transition(sid, "SETUP"):
                return self._destroy(sid)
            self.log(sid, f"preparing scenario {entry.id}")
            tmp = Path(tempfile.mkdtemp(prefix="kops-fixtures-"))
            for f in sorted((scn.dir / "fixtures").glob("*")):
                (tmp / f.name).write_text(scn.text(f"fixtures/{f.name}"))
            env = {f"KOPS_P_{k.upper()}": str(v) for k, v in scn.params.items()} | {"KOPS_FIXTURES": str(tmp)}
            sb.run_setup(scn.dir / scn.raw["setup"]["script"], env)
            if not self.transition(sid, "CONFIRMING"):
                return self._destroy(sid)
            self.log(sid, "confirming the initial state")
            ver = self.verifier_factory(sb, scn.criteria(), scn.raw["verification"].get("settle"))
            ver.capture_baselines()
            _confirm_setup(scn, ver)
            baselines = {k[1]: v for k, v in ver.ctx.items() if isinstance(k, tuple)}
            self.update(sid, baselines_json=json.dumps(baselines), attempt_mark=utcnow())
            if self.transition(sid, "ACTIVE", only_from={"CONFIRMING"}):
                prog.record_attempt(self.db, user_id, entry.id)
                self.log(sid, "ready")
            else:
                self._destroy(sid)
        except InvalidTrial as e:
            self._invalid(sid, f"setup confirmation failed: {e.reason}: {e.detail}"[:500])
        except Exception as e:
            self._invalid(sid, f"setup failed: {_short(e)}")
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)

    def _invalid(self, sid: str, message: str) -> None:
        log.warning("session %s INVALID: %s", sid, message)
        self.log(sid, message)
        if self.transition(sid, "INVALID", message):
            self._release(sid)
        else:
            self._destroy(sid)

    def _release(self, sid: str) -> None:
        """Destroy the sandbox of a session whose state is already final."""
        with self.db.session() as s:
            row = s.get(SessionRow, sid)
            box = row.sandbox_id if row else None
        self._sandboxes.pop(sid, None)
        if box:
            self._destroy_box(box)

    def _destroy_box(self, box: str) -> None:
        with self._lock:
            if box in self._destroying:
                return
            self._destroying.add(box)
        try:
            self.provider.destroy(box)
        except Exception as e:
            log.warning("destroy %s failed: %s", box, e)
        finally:
            self._destroying.discard(box)

    def _destroy(self, sid: str) -> None:
        self._release(sid)
        self.transition(sid, "DESTROYED")

    # -- finishing an attempt ---------------------------------------------------------------
    def _finish_attempt(self, sid: str) -> None:
        with self.db.session() as s:
            row = self._row(s, sid)
            if not (row.type == "practice" and row.scenario_id and row.attempt_mark):
                return
            delta = int((utcnow() - row.attempt_mark).total_seconds())
            uid, scn, viewed = row.user_id, row.scenario_id, row.solution_viewed
            row.attempt_mark = None
            s.commit()
        prog.record_finish(self.db, uid, scn, viewed, delta)

    def end(self, sid: str) -> None:
        """ENDED now, sandbox destroyed in the background."""
        self._finish_attempt(sid)
        with self.db.session() as s:
            if self._row(s, sid).state in TERMINAL:
                return
        if self.transition(sid, "ENDED"):
            self.update(sid, ended_at=utcnow())
            self._pool.submit(self._destroy, sid)

    def delete(self, user: User, sid: str) -> None:
        row = self.get(user, sid)
        if row.state in TERMINAL:
            if row.state == "ENDED":
                self._pool.submit(self._destroy, sid)
            return
        self.end(sid)

    # -- check, hints, solution -----------------------------------------------------------
    def _sandbox(self, row: SessionRow):
        sb = self._sandboxes.get(row.id)
        if sb is None and row.sandbox_id:
            try:
                sb = self.provider.attach(row.sandbox_id)
            except Exception as e:
                raise ApiError("provider_error", f"cannot reach the sandbox: {_short(e)}")
            self._sandboxes[row.id] = sb
        if sb is None:
            raise ApiError("bad_state", "the session has no sandbox yet")
        return sb

    def _practice(self, user: User, sid: str) -> tuple[SessionRow, Entry]:
        row = self.get(user, sid)
        entry = self.catalog.get(row.scenario_id or "") if row.type == "practice" else None
        if entry is None:
            raise ApiError("bad_state", "this session is not a practice session")
        return row, entry

    def check(self, user: User, sid: str, wait: bool) -> dict:
        row, entry = self._practice(user, sid)
        with self.db.session() as s:     # compare-and-set ACTIVE -> CHECKING
            res = s.execute(update(SessionRow).where(SessionRow.id == sid, SessionRow.state == "ACTIVE")
                            .values(state="CHECKING", rev=SessionRow.rev + 1))
            s.commit()
        if res.rowcount != 1:
            raise ApiError("bad_state", f"cannot check while the session is {self.state_of(sid)}")
        t0 = time.monotonic()
        try:
            sb = self._sandbox(row)
            scn = self.scenario(entry, row.seed or 1)
            ver = self.verifier_factory(sb, scn.criteria(), scn.raw["verification"].get("settle"))
            for cid, dg in json.loads(row.baselines_json).items():
                ver.ctx[("baseline", cid)] = dg
            results = ver.evaluate(settle=wait)
            outcome = Verifier.outcome(results)
        except ApiError:
            self.transition(sid, "ACTIVE", only_from={"CHECKING"})
            raise
        except Exception as e:
            results, outcome = [], "INVALID"
            log.warning("check failed on %s: %s", sid, e)
        seconds = round(time.monotonic() - t0, 1)
        crit = [{"id": r.id, "required": r.required, "status": r.status, "evidence": r.evidence}
                for r in results]
        req = [r for r in results if r.required]
        out = {"outcome": outcome, "criteria": crit,
               "required_passed": sum(1 for r in req if r.status == "pass"),
               "required_total": len(req), "checked_at": iso(utcnow()), "seconds": seconds}
        with self.db.session() as s:
            cur = self._row(s, sid)
            delta = int((utcnow() - cur.attempt_mark).total_seconds()) if cur.attempt_mark else 0
            s.add(CheckRow(session_id=sid, user_id=cur.user_id, scenario_id=entry.id, attempt=cur.attempt,
                           outcome=outcome, criteria_json=json.dumps(crit),
                           required_passed=out["required_passed"], required_total=out["required_total"],
                           seconds=seconds, solution_viewed=cur.solution_viewed,
                           hints_used=len(json.loads(cur.hints_read_json))))
            cur.last_check_json = json.dumps(out)
            cur.attempt_mark = utcnow()
            viewed = cur.solution_viewed
            s.commit()
        if outcome != "INVALID":
            prog.record_check(self.db, cur.user_id, entry.id, outcome, viewed, delta)
        self.transition(sid, "ACTIVE", only_from={"CHECKING"})
        return out

    def hint(self, user: User, sid: str, n: int) -> dict:
        row, entry = self._practice(user, sid)
        if row.state not in OPEN:
            raise ApiError("bad_state", "hints are available while the task is active")
        hints = self.catalog.hints(entry, json.loads(row.params_json))
        if not 1 <= n <= len(hints):
            raise ApiError("not_found", "no such hint")
        with self.db.session() as s:
            cur = self._row(s, sid)
            read = json.loads(cur.hints_read_json)
            if n not in read:
                cur.hints_read_json = json.dumps(sorted(read + [n]))
                cur.rev += 1
                s.commit()
        return {"n": n, "text_md": hints[n - 1]}

    def solution(self, user: User, sid: str) -> dict:
        row, entry = self._practice(user, sid)
        if row.state not in OPEN:
            raise ApiError("bad_state", "the solution is available while the task is active")
        self.update(sid, solution_viewed=True)
        return {"explanation_md": self.catalog.explanation(entry, json.loads(row.params_json))}

    # -- next / restart / extend -----------------------------------------------------------
    def next(self, user: User, sid: str, scenario_id: str | None, seed: int | None = None) -> dict:
        row, cur = self._practice(user, sid)
        entry = cur if scenario_id is None else self.catalog.get(scenario_id)   # restart: same scenario
        if entry is None:
            raise ApiError("invalid_request", f"unknown scenario {scenario_id!r}")
        if not entry.available:
            raise ApiError("invalid_request", f"scenario not available: {entry.note}")
        with self.db.session() as s:   # compare-and-set ACTIVE -> RESETTING
            res = s.execute(update(SessionRow).where(SessionRow.id == sid, SessionRow.state == "ACTIVE")
                            .values(state="RESETTING", message=None, rev=SessionRow.rev + 1))
            s.commit()
        if res.rowcount != 1:
            raise ApiError("bad_state", f"cannot switch tasks while the session is {self.state_of(sid)}")
        self._finish_attempt(sid)
        if scenario_id is None:
            seed = row.seed
        self._pool.submit(self._reset_flow, sid, entry, row.reset_mode, seed)
        return self.view(user, sid)

    def _reset_flow(self, sid: str, entry: Entry, old_mode: str | None, seed: int | None) -> None:
        try:
            seed = int(seed) if seed is not None else random.randrange(1, 2 ** 31)
            with self.db.session() as s:
                pristine = self._row(s, sid).pristine_json
            sb = self._sandboxes[sid]
            done = False
            if old_mode == "api" and entry.reset == "api" and pristine:
                self.log(sid, "resetting the cluster state through the API")
                base = Baseline.from_json(pristine)
                done = Reset(sb).wait_restored(base, self.cfg.reset_timeout_seconds,
                                               self.cfg.reset_poll_seconds)
                if not done:
                    self.log(sid, "API reset did not reach the baseline; recreating the cluster")
            if not done:
                self.log(sid, "recreating the cluster")
                sb = self.provider.recreate(sb, lambda line: self.log(sid, line))
                self._sandboxes[sid] = sb
                self.update(sid, sandbox_id=sb.id, pristine_json=None)
            scn = self.scenario(entry, seed)
            with self.db.session() as s:
                cur = self._row(s, sid)
                cur.scenario_id, cur.seed, cur.params_json = entry.id, seed, json.dumps(scn.params)
                cur.reset_mode, cur.attempt = entry.reset, cur.attempt + 1
                cur.hints_read_json, cur.solution_viewed, cur.last_check_json = "[]", False, None
                cur.rev += 1
                s.commit()
            if self.state_of(sid) in GONE:
                return self._destroy(sid)
            self._setup_flow(sid, entry)
        except Exception as e:
            self._invalid(sid, f"reset failed: {_short(e)}")

    def extend(self, user: User, sid: str) -> dict:
        row = self.get(user, sid)
        if row.state not in OPEN:
            raise ApiError("bad_state", "only an active session can be extended")
        if row.extensions >= self.cfg.max_extensions:
            raise ApiError("quota_exceeded", "no extensions left")
        ttl = self.cfg.practice_ttl_minutes if row.type == "practice" else self.cfg.playground_ttl_minutes
        self.update(sid, extensions=row.extensions + 1, expires_at=row.expires_at + timedelta(minutes=ttl))
        return self.view(user, sid)

    # -- sweeper, recovery, admin -----------------------------------------------------------
    def sweep(self) -> dict:
        """Expire overdue sessions; destroy sandboxes with no live session."""
        expired = orphans = 0
        with self.db.session() as s:
            overdue = s.scalars(select(SessionRow.id).where(
                SessionRow.state.not_in(TERMINAL), SessionRow.expires_at < utcnow())).all()
        for sid in overdue:
            self.end(sid)
            expired += 1
        try:
            refs = self.provider.list_owned()
        except Exception as e:
            log.warning("sweeper cannot list sandboxes: %s", e)
            return {"expired": expired, "orphans": 0}
        for ref in refs:
            with self.db.session() as s:
                row = s.get(SessionRow, ref.session_id)
                dead = row is None or row.state in TERMINAL or row.sandbox_id not in (None, ref.sandbox_id)
            if dead:
                log.info("sweeper destroys orphan sandbox %s", ref.sandbox_id)
                self._destroy_box(ref.sandbox_id)
                orphans += 1
                if row is not None and row.state == "ENDED":
                    self.transition(row.id, "DESTROYED")
        return {"expired": expired, "orphans": orphans}

    def orphan_count(self) -> int:
        try:
            refs = self.provider.list_owned()
        except Exception:
            return 0
        n = 0
        for ref in refs:
            with self.db.session() as s:
                row = s.get(SessionRow, ref.session_id)
            if row is None or row.state in TERMINAL:
                n += 1
        return n

    def recover(self) -> None:
        """After a restart: re-attach live sessions, fail the ones caught mid-transition."""
        with self.db.session() as s:
            rows = s.scalars(select(SessionRow).where(SessionRow.state.not_in(TERMINAL))).all()
        for row in rows:
            if row.state in OPEN:
                try:
                    self._sandboxes[row.id] = self.provider.attach(row.sandbox_id or "")
                    self.transition(row.id, "ACTIVE", only_from={"CHECKING"})
                except Exception as e:
                    self._invalid(row.id, f"sandbox lost during platform restart: {_short(e)}")
            else:
                self._invalid(row.id, f"platform restarted while the session was {row.state}")

    def admin_users(self) -> list[dict]:
        with self.db.session() as s:
            users = s.scalars(select(User).order_by(User.created_at)).all()
            out = []
            for u in users:
                rows = s.scalars(select(SessionRow).where(SessionRow.user_id == u.id)).all()
                act = next((r.id for r in rows if r.state not in TERMINAL), None)
                out.append({"id": u.id, "username": u.username, "email": u.email,
                            "created_at": iso(u.created_at), "last_seen_at": iso(u.last_seen_at),
                            "active_session": act, "sessions_total": len(rows)})
        return out

    def admin_capacity(self) -> dict:
        cap, _, active = self._capacity()
        return {"provider": self.provider.name, "max_sessions": cap.max_sessions,
                "active_sessions": active, "nodes": cap.nodes, "orphans": self.orphan_count()}


def _short(e: Exception) -> str:
    return f"{type(e).__name__}: {str(e)[:300]}"
