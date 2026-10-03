"""Mock of the KOPS platform API (docs/platform-api.md) for developing web/ without the backend.

Run:  .venv/bin/python web/dev/mock_server.py --port 8099
Everything is in memory. Login is automatic (user "alice"; add ?admin=0 ... /mock/whoami to flip, see below).
Extra mock-only endpoints:  POST /mock/fail {"code":"capacity_exceeded"}  makes the next POST /api/sessions fail.
                            POST /mock/admin {"is_admin":false}            toggles the admin flag.
"""
import argparse
import asyncio
import itertools
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

WEB = Path(__file__).resolve().parent.parent
app = FastAPI(title="KOPS mock")
FAST = {"factor": 1.0}  # --fast shortens provisioning delays
STATE = {"admin": True, "fail": None, "me": {"id": "11111111-aaaa", "username": "alice", "email": "alice@example.com"}}


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def err(status, code, detail):
    return JSONResponse({"error": code, "detail": detail}, status_code=status)


SCENARIOS = [
    {"id": "kops-net-service-endpoint-repair-001", "title": "Restore traffic to a web Service that has no endpoints", "difficulty": 2,
     "tags": ["service", "endpoints"], "profiles": {"cka": {"domain": "troubleshooting", "competency": "CKA-TRB-05"}, "ckad": {"domain": "services-networking", "competency": "CKAD-SNW-02"}},
     "available": True, "availability_note": None, "reset": "api", "hint_count": 3},
    {"id": "ckad-cfg-projected-volume-001", "title": "Mount a ConfigMap and Secret through one projected volume", "difficulty": 1,
     "tags": ["configmap", "secret", "volume"], "profiles": {"ckad": {"domain": "configuration", "competency": "CKAD-CFG-03"}},
     "available": True, "availability_note": None, "reset": "api", "hint_count": 3},
    {"id": "cka-trb-node-unschedulable-001", "title": "Bring a cordoned node back into scheduling", "difficulty": 3,
     "tags": ["node", "cordon"], "profiles": {"cka": {"domain": "troubleshooting", "competency": "CKA-TRB-02"}},
     "available": False, "availability_note": "validated on kind only", "reset": "vm", "hint_count": 2},
    {"id": "cka-sto-default-class-001", "title": "Make a StorageClass the default", "difficulty": 1,
     "tags": ["storage"], "profiles": {"cka": {"domain": "storage", "competency": "CKA-STO-01"}},
     "available": True, "availability_note": None, "reset": "api", "hint_count": 3},
]
PROGRESS = {"kops-net-service-endpoint-repair-001": {"status": "attempted", "attempts": 2, "best_outcome": "FAIL", "last_checked_at": "2026-10-02T10:00:00Z", "seconds_spent": 540},
            "ckad-cfg-projected-volume-001": {"status": "solved", "attempts": 1, "best_outcome": "PASS", "last_checked_at": "2026-10-01T09:00:00Z", "seconds_spent": 300}}
TASK_MD = """## Scenario

Namespace `shop` contains a Deployment `web` and a Service `web`. Traffic to the Service fails.

### Objectives

1. Find out why the Service has **no endpoints**.
2. Fix it **without** recreating the Service.

```bash
kubectl -n shop get svc,ep,deploy web
```

See the [Kubernetes docs](https://kubernetes.io/docs/concepts/services-networking/service/). <script>alert(1)</script>
"""
HINTS = ["Compare the Service `selector` with the Pod labels.", "Use `kubectl -n shop get pods --show-labels`.", "Patch the Service selector: `kubectl -n shop edit svc web`."]
SOLUTION = "## Explanation\n\nThe selector said `app=wb`; the Pods carry `app=web`. Edit the Service:\n\n```bash\nkubectl -n shop patch svc web -p '{\"spec\":{\"selector\":{\"app\":\"web\"}}}'\n```\n"

SESSIONS: dict = {}
IDS = itertools.count(1)


def sc(sid):
    return next((s for s in SCENARIOS if s["id"] == sid), None)


def plan_for(kind, delay=1.0):
    f = FAST["factor"]
    if kind == "provision":
        return [(0, "REQUESTED", "request accepted"), (1 * f, "PROVISIONING", "cloning golden image"), (2.5 * f, "PROVISIONING", "VM scheduled on kops-worker-1"),
                (4 * f, "SETUP", "running scenario setup"), (6 * f, "CONFIRMING", "negative control: check must fail"), (7.5 * f, "ACTIVE", "ready")]
    if kind == "reset":
        return [(0, "RESETTING", "resetting task"), (2 * f, "SETUP", "re-running setup"), (3.5 * f, "ACTIVE", "ready")]
    return []


def schedule(s, kind):
    s["_t0"] = time.monotonic()
    s["_plan"] = plan_for(kind)
    s["_applied"] = 0


def advance(s):
    """Apply plan steps whose time has come (lazy state machine)."""
    t = time.monotonic() - s["_t0"]
    while s["_applied"] < len(s["_plan"]) and s["_plan"][s["_applied"]][0] <= t:
        _, state, line = s["_plan"][s["_applied"]]
        s["_applied"] += 1
        s["state"] = state
        s["_logs"].append({"ts": iso(now()), "line": line})
        if state == "ACTIVE":
            s["task"] = s["_task"]


def public(s):
    advance(s)
    return {k: v for k, v in s.items() if not k.startswith("_")}


def user_sessions():
    return sorted(SESSIONS.values(), key=lambda s: (s["state"] in ("ENDED", "DESTROYED"), -s["_n"]))


def active_session():
    return next((s for s in user_sessions() if (advance(s) or True) and s["state"] not in ("ENDED", "DESTROYED", "INVALID")), None)


# ---- auth -------------------------------------------------------------------------------------
@app.get("/auth/login")
def login():
    return RedirectResponse("/")


@app.get("/auth/logout")
def logout():
    return RedirectResponse("/")


@app.post("/mock/fail")
async def mock_fail(req: Request):
    STATE["fail"] = (await req.json()).get("code")
    return {"ok": True}


@app.post("/mock/admin")
async def mock_admin(req: Request):
    STATE["admin"] = bool((await req.json()).get("is_admin"))
    return {"ok": True}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/me")
def me():
    return {**STATE["me"], "is_admin": STATE["admin"]}


@app.get("/api/config")
def config():
    return {"version": "0.1.0-mock", "provider": "mock", "quotas": {"active_sessions_per_user": 1, "practice_ttl_minutes": 120, "playground_ttl_minutes": 120, "max_extensions": 2},
            "features": {"playground": True, "mock_exam": False, "docs": False, "editor": False}}


def scenario_view(s, with_hints=False):
    prof = PROGRESS.get(s["id"], {})
    out = {k: v for k, v in s.items() if k != "hint_count"}
    out["status"] = prof.get("status", "none")
    if with_hints:
        out["hint_count"] = s["hint_count"]
    return out


@app.get("/api/scenarios")
def scenarios(profile: str = "", domain: str = "", difficulty: int = 0, q: str = ""):
    out = []
    for s in SCENARIOS:
        if profile and profile not in s["profiles"]:
            continue
        if domain and not any(p["domain"] == domain for p in s["profiles"].values()):
            continue
        if difficulty and s["difficulty"] != difficulty:
            continue
        if q and q.lower() not in (s["title"] + " ".join(s["tags"])).lower():
            continue
        out.append(scenario_view(s))
    return out


@app.get("/api/scenarios/{sid}")
def scenario(sid: str):
    s = sc(sid)
    return scenario_view(s, True) if s else err(404, "not_found", "no such scenario")


# ---- sessions ---------------------------------------------------------------------------------
@app.post("/api/sessions", status_code=201)
async def create_session(req: Request):
    body = await req.json()
    if STATE["fail"]:
        code, STATE["fail"] = STATE["fail"], None
        return err({"capacity_exceeded": 503, "provider_error": 502, "quota_exceeded": 409}.get(code, 500), code, f"mock failure: {code}")
    if active_session():
        return err(409, "quota_exceeded", "you already have an active session")
    typ = body.get("type")
    n = next(IDS)
    sid = f"s_{n:06x}"
    created = now()
    s = {"id": sid, "type": typ, "state": "REQUESTED", "owner": "alice", "created_at": iso(created), "expires_at": iso(created + timedelta(minutes=120)), "extensions": 0,
         "scenario_id": None, "task": None, "targets": [{"name": "base", "role": "base"}, {"name": "cp-1", "role": "node"}, {"name": "worker-1", "role": "node"}],
         "hints_used": 0, "solution_viewed": False, "attempt": 1, "last_check": None, "reset": "api", "message": None,
         "_n": n, "_logs": [], "_checks": 0, "_hints": set(), "_task": None}
    if typ == "practice":
        scn = sc(body.get("scenario_id"))
        if not scn:
            return err(422, "invalid_request", "unknown scenario_id")
        if not scn["available"]:
            return err(422, "invalid_request", scn["availability_note"])
        s["scenario_id"] = scn["id"]
        s["reset"] = scn["reset"]
        s["_task"] = {"title": scn["title"], "text_md": TASK_MD, "domain": list(scn["profiles"].values())[0]["domain"], "difficulty": scn["difficulty"]}
    elif typ != "playground":
        return err(422, "invalid_request", "type must be practice or playground")
    SESSIONS[sid] = s
    schedule(s, "provision")
    if typ == "playground":
        s["_plan"] = [p for p in s["_plan"] if p[1] not in ("SETUP", "CONFIRMING")]
    advance(s)
    return public(s)


@app.get("/api/sessions")
def list_sessions():
    return [public(s) for s in user_sessions()]


def get_s(sid):
    s = SESSIONS.get(sid)
    if s:
        advance(s)
    return s


@app.get("/api/sessions/{sid}")
def get_session(sid: str):
    s = get_s(sid)
    return public(s) if s else err(404, "not_found", "no such session")


@app.get("/api/sessions/{sid}/events")
async def events(sid: str):
    s = get_s(sid)
    if not s:
        return err(404, "not_found", "no such session")

    async def gen():
        sent_logs, last = 0, None
        yield ": open\n\n"
        while True:
            advance(s)
            while sent_logs < len(s["_logs"]):
                yield f"event: log\ndata: {json.dumps(s['_logs'][sent_logs])}\n\n"
                sent_logs += 1
            snap = json.dumps(public(s), sort_keys=True)
            if snap != last:
                last = snap
                yield f"event: state\ndata: {snap}\n\n"
            if s["state"] in ("DESTROYED", "INVALID"):
                return
            await asyncio.sleep(0.5)
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/sessions/{sid}/check")
async def check(sid: str):
    s = get_s(sid)
    if not s:
        return err(404, "not_found", "no such session")
    if s["type"] != "practice" or s["state"] != "ACTIVE":
        return err(409, "bad_state", f"cannot check in state {s['state']}")
    s["state"] = "CHECKING"
    await asyncio.sleep(1.5 * FAST["factor"])
    s["_checks"] += 1
    ok = s["_checks"] >= 2
    crit = [{"id": "endpoints_count", "required": True, "status": "pass" if ok else "fail", "evidence": "3 endpoints" if ok else "0 endpoints for Service shop/web"},
            {"id": "service_unchanged", "required": True, "status": "pass", "evidence": "Service UID unchanged"},
            {"id": "pods_ready", "required": True, "status": "pass" if ok else "error", "evidence": "3/3 ready" if ok else "kubectl timed out"},
            {"id": "no_extra_replicas", "required": False, "status": "pass", "evidence": "replicas=3"}]
    res = {"outcome": "PASS" if ok else "FAIL", "criteria": crit, "required_passed": 3 if ok else 1, "required_total": 3, "checked_at": iso(now()), "seconds": 1.5}
    s["last_check"] = res
    s["state"] = "ACTIVE"
    PROGRESS[s["scenario_id"]] = {"status": "solved_assisted" if s["solution_viewed"] and ok else "solved" if ok else "attempted", "attempts": s["attempt"], "best_outcome": res["outcome"],
                                  "last_checked_at": res["checked_at"], "seconds_spent": 120 * s["_checks"]}
    return res


@app.get("/api/sessions/{sid}/hints/{n}")
def hint(sid: str, n: int):
    s = get_s(sid)
    if not s:
        return err(404, "not_found", "no such session")
    scn = sc(s["scenario_id"]) if s["scenario_id"] else None
    if not scn or n < 1 or n > scn["hint_count"]:
        return err(404, "not_found", "no such hint")
    s["_hints"].add(n)
    s["hints_used"] = len(s["_hints"])
    return {"n": n, "text_md": HINTS[n - 1]}


@app.post("/api/sessions/{sid}/solution")
def solution(sid: str):
    s = get_s(sid)
    if not s:
        return err(404, "not_found", "no such session")
    s["solution_viewed"] = True
    return {"explanation_md": SOLUTION}


@app.post("/api/sessions/{sid}/next")
async def next_task(sid: str, req: Request):
    s = get_s(sid)
    body = await req.json()
    scn = sc(body.get("scenario_id"))
    if not s or not scn:
        return err(404, "not_found", "no such session or scenario")
    if s["state"] != "ACTIVE":
        return err(409, "bad_state", "session is not ACTIVE")
    s.update(scenario_id=scn["id"], attempt=1, hints_used=0, solution_viewed=False, last_check=None, task=None, reset=scn["reset"])
    s["_hints"], s["_checks"] = set(), 0
    s["_task"] = {"title": scn["title"], "text_md": TASK_MD, "domain": list(scn["profiles"].values())[0]["domain"], "difficulty": scn["difficulty"]}
    schedule(s, "reset")
    advance(s)
    return public(s)


@app.post("/api/sessions/{sid}/restart")
def restart(sid: str):
    s = get_s(sid)
    if not s:
        return err(404, "not_found", "no such session")
    if s["state"] != "ACTIVE":
        return err(409, "bad_state", "session is not ACTIVE")
    s["attempt"] += 1
    s["last_check"] = None
    s["_checks"] = 0
    schedule(s, "reset")
    advance(s)
    return public(s)


@app.post("/api/sessions/{sid}/extend")
def extend(sid: str):
    s = get_s(sid)
    if not s:
        return err(404, "not_found", "no such session")
    if s["extensions"] >= 2:
        return err(409, "quota_exceeded", "no extensions left")
    s["extensions"] += 1
    s["expires_at"] = iso(datetime.strptime(s["expires_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) + timedelta(minutes=120))
    return public(s)


def destroy(s):
    s["state"] = "ENDED"
    s["_t0"] = time.monotonic()
    s["_plan"] = [(2 * FAST["factor"], "DESTROYED", "sandbox destroyed")]
    s["_applied"] = 0


@app.delete("/api/sessions/{sid}", status_code=202)
def delete(sid: str):
    s = get_s(sid)
    if not s:
        return err(404, "not_found", "no such session")
    destroy(s)
    return JSONResponse({"state": "ENDED"}, status_code=202)


@app.websocket("/api/sessions/{sid}/terminal")
async def terminal(ws: WebSocket, sid: str, target: str = "base", tab: int = 1):
    s = get_s(sid)
    if not s or s["state"] not in ("ACTIVE", "CHECKING"):
        await ws.close(code=4404)
        return
    await ws.accept()
    prompt = f"\x1b[32mcandidate@{target}\x1b[0m:~$ "
    await ws.send_text(json.dumps({"t": "o", "d": f"Mock terminal (tab {tab}) on {target}. Type 'exit' to close.\r\n{prompt}"}))
    line = ""
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            if msg.get("t") == "r":
                continue
            for ch in msg.get("d", ""):
                if ch in "\r\n":
                    cmd, line = line.strip(), ""
                    if cmd == "exit":
                        await ws.send_text(json.dumps({"t": "o", "d": "\r\nlogout\r\n"}))
                        await ws.send_text(json.dumps({"t": "x", "code": 0}))
                        await ws.close()
                        return
                    out = f"\r\n{cmd}: mock output\r\n" if cmd else "\r\n"
                    await ws.send_text(json.dumps({"t": "o", "d": out + prompt}))
                elif ch in "\x7f\b":
                    if line:
                        line = line[:-1]
                        await ws.send_text(json.dumps({"t": "o", "d": "\b \b"}))
                elif ch >= " ":
                    line += ch
                    await ws.send_text(json.dumps({"t": "o", "d": ch}))
    except WebSocketDisconnect:
        return


# ---- progress and admin -----------------------------------------------------------------------
@app.get("/api/progress")
def progress():
    summary = {"cka": {}, "ckad": {}}
    for s in SCENARIOS:
        for p, v in s["profiles"].items():
            d = summary[p].setdefault(v["domain"], {"solved": 0, "assisted": 0, "attempted": 0, "total": 0})
            d["total"] += 1
            st = PROGRESS.get(s["id"], {}).get("status")
            if st == "solved":
                d["solved"] += 1
            elif st == "solved_assisted":
                d["assisted"] += 1
            elif st == "attempted":
                d["attempted"] += 1
    return {"scenarios": [{"scenario_id": k, **v} for k, v in PROGRESS.items()], "summary": summary}


def admin_only():
    return None if STATE["admin"] else err(403, "forbidden", "admin only")


@app.get("/api/admin/sessions")
def admin_sessions():
    return admin_only() or [public(s) for s in user_sessions()] + [
        {"id": "s_other1", "type": "practice", "state": "ACTIVE", "owner": "bob", "created_at": "2026-10-03T07:00:00Z", "expires_at": "2026-10-03T09:00:00Z", "scenario_id": SCENARIOS[1]["id"]}]


@app.delete("/api/admin/sessions/{sid}", status_code=202)
def admin_delete(sid: str):
    if (r := admin_only()):
        return r
    s = SESSIONS.get(sid)
    if s:
        destroy(s)
    return JSONResponse({"state": "ENDED"}, status_code=202)


@app.get("/api/admin/users")
def admin_users():
    a = active_session()
    return admin_only() or [{"id": "1", "username": "alice", "email": "alice@example.com", "created_at": "2026-09-01T00:00:00Z", "last_seen_at": iso(now()), "active_session": a["id"] if a else None, "sessions_total": len(SESSIONS)},
                            {"id": "2", "username": "bob", "email": None, "created_at": "2026-09-10T00:00:00Z", "last_seen_at": "2026-10-03T07:10:00Z", "active_session": "s_other1", "sessions_total": 4}]


@app.get("/api/admin/capacity")
def admin_capacity():
    return admin_only() or {"provider": "mock", "max_sessions": 2, "active_sessions": 2 if active_session() else 1,
                            "nodes": [{"name": "kops-worker-1", "memory_allocatable_mib": 15000, "memory_requested_mib": 9000}, {"name": "kops-worker-2", "memory_allocatable_mib": 15000, "memory_requested_mib": 13500}], "orphans": 0}


app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--fast", action="store_true", help="shorten provisioning delays 5x")
    a = ap.parse_args()
    if a.fast:
        FAST["factor"] = 0.2
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")
