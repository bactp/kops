"""The /api routes. Thin: validation and ownership here, behaviour in SessionService."""
from __future__ import annotations

import asyncio
import json

import anyio
from fastapi import APIRouter, Depends, Query, Request, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, text

from . import progress as prog
from .auth import current_user, require_admin
from .db import SessionEvent, SessionRow, User, iso
from .errors import ApiError
from .service import OPEN, SessionService
from .settings import VERSION
from .terminal import serve_terminal


class CreateBody(BaseModel):
    type: str
    scenario_id: str | None = None
    seed: int | None = None


class CheckBody(BaseModel):
    wait: bool = False


class NextBody(BaseModel):
    scenario_id: str


def svc(request: Request) -> SessionService:
    return request.app.state.service


def router() -> APIRouter:
    r = APIRouter(prefix="/api")
    me = Depends(current_user)

    @r.get("/me")
    def get_me(user: User = me):
        return {"id": user.id, "username": user.username, "email": user.email, "is_admin": user.is_admin}

    @r.get("/config")
    def get_config(request: Request, user: User = me):
        c = request.app.state.settings
        return {"version": VERSION, "provider": request.app.state.provider.name,
                "quotas": {"active_sessions_per_user": c.sessions_per_user,
                           "practice_ttl_minutes": c.practice_ttl_minutes,
                           "playground_ttl_minutes": c.playground_ttl_minutes,
                           "max_extensions": c.max_extensions},
                "features": c.features}

    # -- catalogue -------------------------------------------------------------------------
    @r.get("/scenarios")
    def list_scenarios(request: Request, profile: str | None = None, domain: str | None = None,
                       difficulty: int | None = Query(None, ge=1, le=3), q: str | None = None,
                       user: User = me):
        st = prog.statuses(request.app.state.db, user.id)
        cat = request.app.state.catalog
        return [e.public() | {"status": st.get(e.id, "none")}
                for e in cat.search(profile, domain, difficulty, q)]

    @r.get("/scenarios/{sid}")
    def get_scenario(request: Request, sid: str, user: User = me):
        e = request.app.state.catalog.get(sid)
        if e is None:
            raise ApiError("not_found", "no such scenario")
        st = prog.statuses(request.app.state.db, user.id)
        return e.public() | {"status": st.get(e.id, "none"), "hint_count": e.hint_count}

    # -- sessions --------------------------------------------------------------------------
    @r.post("/sessions", status_code=201)
    def create_session(request: Request, body: CreateBody, user: User = me):
        return svc(request).create(user, body.type, body.scenario_id, body.seed)

    @r.get("/sessions")
    def list_sessions(request: Request, user: User = me):
        return svc(request).list_for(user)

    @r.get("/sessions/{sid}")
    def get_session(request: Request, sid: str, user: User = me):
        return svc(request).view(user, sid)

    @r.post("/sessions/{sid}/check")
    def check(request: Request, sid: str, body: CheckBody | None = None, user: User = me):
        return svc(request).check(user, sid, bool(body and body.wait))

    @r.get("/sessions/{sid}/hints/{n}")
    def hint(request: Request, sid: str, n: int, user: User = me):
        return svc(request).hint(user, sid, n)

    @r.post("/sessions/{sid}/solution")
    def solution(request: Request, sid: str, user: User = me):
        return svc(request).solution(user, sid)

    @r.post("/sessions/{sid}/next")
    def next_task(request: Request, sid: str, body: NextBody, user: User = me):
        return svc(request).next(user, sid, body.scenario_id)

    @r.post("/sessions/{sid}/restart")
    def restart(request: Request, sid: str, user: User = me):
        return svc(request).next(user, sid, None)

    @r.post("/sessions/{sid}/extend")
    def extend(request: Request, sid: str, user: User = me):
        return svc(request).extend(user, sid)

    @r.delete("/sessions/{sid}", status_code=202)
    def delete_session(request: Request, sid: str, user: User = me):
        svc(request).delete(user, sid)
        return {"id": sid, "state": "ENDED"}

    @r.get("/sessions/{sid}/events")
    async def events(request: Request, sid: str, user: User = me):
        service = svc(request)
        service.get(user, sid)      # 404 for strangers, before streaming starts
        poll = request.app.state.settings.sse_poll_seconds

        def snapshot(last_id: int):
            with service.db.session() as s:
                rows = s.scalars(select(SessionEvent).where(SessionEvent.session_id == sid,
                                                            SessionEvent.id > last_id)
                                 .order_by(SessionEvent.id)).all()
                row = s.get(SessionRow, sid)
                logs = [(e.id, {"ts": iso(e.ts), "line": e.line}) for e in rows]
                return logs, service.to_json(row, user.username), row.rev, row.state

        async def stream():
            last_id, last_rev, idle = 0, -1, 0.0
            while True:
                logs, view, rev, state = await anyio.to_thread.run_sync(snapshot, last_id)
                for eid, payload in logs:
                    last_id = eid
                    yield f"event: log\ndata: {json.dumps(payload)}\n\n"
                if rev != last_rev:
                    last_rev = rev
                    yield f"event: state\ndata: {json.dumps(view)}\n\n"
                if state in ("DESTROYED", "INVALID"):
                    return
                idle += poll
                if idle >= 15:
                    idle = 0
                    yield ": keepalive\n\n"
                if await request.is_disconnected():
                    return
                await asyncio.sleep(poll)

        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @r.websocket("/sessions/{sid}/terminal")
    async def terminal(ws: WebSocket, sid: str, target: str = "base", tab: str = "1"):
        service: SessionService = ws.app.state.service
        try:
            user = current_user(ws)
            row = service.get(user, sid)
            if row.state not in OPEN:
                raise ApiError("bad_state", "session is not active")
            sb = service._sandbox(row)
            if target not in [t.name for t in sb.targets()]:
                raise ApiError("not_found", "no such target")
            argv = sb.terminal_argv(target)
        except ApiError as e:
            await ws.close(code=4401 if e.code == "unauthenticated" else 4404 if e.code == "not_found" else 4409)
            return
        await ws.accept()
        await serve_terminal(ws, argv)

    # -- progress --------------------------------------------------------------------------
    @r.get("/progress")
    def progress(request: Request, user: User = me):
        return prog.report(request.app.state.db, request.app.state.catalog, user.id)

    # -- admin -----------------------------------------------------------------------------
    @r.get("/admin/sessions")
    def admin_sessions(request: Request, user: User = Depends(require_admin)):
        return svc(request).list_for(user, all_users=True)

    @r.delete("/admin/sessions/{sid}", status_code=202)
    def admin_delete(request: Request, sid: str, user: User = Depends(require_admin)):
        svc(request).delete(user, sid)
        return {"id": sid, "state": "ENDED"}

    @r.get("/admin/users")
    def admin_users(request: Request, user: User = Depends(require_admin)):
        return svc(request).admin_users()

    @r.get("/admin/capacity")
    def admin_capacity(request: Request, user: User = Depends(require_admin)):
        return svc(request).admin_capacity()

    return r


def health_router() -> APIRouter:
    r = APIRouter()

    @r.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @r.get("/readyz")
    def readyz(request: Request):
        try:
            with request.app.state.db.session() as s:
                s.execute(text("SELECT 1"))
            request.app.state.provider.capacity()
        except Exception as e:
            return JSONResponse({"status": "unavailable", "detail": type(e).__name__}, status_code=503)
        return {"status": "ok"}

    return r
