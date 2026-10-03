import json
import time

import pytest

H = lambda n="alice", a=False: __import__("conftest").Env.h(n, a)  # noqa: E731


def test_auth_required(env):
    c = env.client
    for method, path in [("get", "/api/me"), ("get", "/api/scenarios"), ("get", "/api/sessions"),
                         ("post", "/api/sessions"), ("get", "/api/progress"), ("get", "/api/admin/users")]:
        r = getattr(c, method)(path)
        assert r.status_code == 401 and r.json()["error"] == "unauthenticated", path
    assert c.get("/healthz").json() == {"status": "ok"}
    assert c.get("/readyz").status_code == 200


def test_dev_auth_refused_without_flag(tmp_path, scenarios):
    from conftest import Env
    with pytest.raises(RuntimeError):
        Env(tmp_path, scenarios, allow_dev_auth=False)


def test_me_config_and_admin_flag(env):
    me = env.client.get("/api/me", headers=env.h("bob")).json()
    assert me["username"] == "bob" and me["is_admin"] is False and me["id"]
    assert env.client.get("/api/me", headers=env.h("root", True)).json()["is_admin"] is True
    cfg = env.client.get("/api/config", headers=env.h()).json()
    assert cfg["provider"] == "fake" and cfg["quotas"]["active_sessions_per_user"] == 1
    assert cfg["features"]["playground"] is True and cfg["features"]["mock_exam"] is False


def test_scenarios_filters_and_no_task_text(env):
    h = env.h()
    allr = env.client.get("/api/scenarios", headers=h).json()
    assert {s["id"] for s in allr} == {"t-api-a-001", "t-api-b-001", "t-vm-001"}
    a = next(s for s in allr if s["id"] == "t-api-a-001")
    assert a["reset"] == "api" and a["status"] == "none" and a["available"] is True
    assert a["profiles"]["cka"]["domain"] == "troubleshooting"
    assert next(s for s in allr if s["id"] == "t-vm-001")["reset"] == "vm"
    q = lambda **p: {s["id"] for s in env.client.get("/api/scenarios", params=p, headers=h).json()}  # noqa: E731
    assert q(profile="ckad") == {"t-api-a-001"}
    assert q(difficulty=2) == {"t-api-a-001"}
    assert q(domain="services-networking") == {"t-api-a-001"}
    assert q(q="vm") == {"t-vm-001"}
    one = env.client.get("/api/scenarios/t-api-a-001", headers=h).json()
    assert one["hint_count"] == 3 and "Fix the ConfigMap" not in json.dumps(one)
    assert env.client.get("/api/scenarios/nope", headers=h).json()["error"] == "not_found"


def test_unavailable_scenarios(tmp_path, scenarios):
    from conftest import Env
    f = tmp_path / "available.txt"
    f.write_text("# c\nt-vm-001\n")
    e = Env(tmp_path, scenarios, catalog_file=str(f))
    by = {s["id"]: s for s in e.client.get("/api/scenarios", headers=e.h()).json()}
    assert by["t-vm-001"]["available"] is True
    assert by["t-api-a-001"]["available"] is False
    assert by["t-api-a-001"]["availability_note"] == "not yet validated on this provider"
    r = e.create(scenario="t-api-a-001")
    assert r.status_code == 422 and r.json()["error"] == "invalid_request"
    f.write_text("*\n")
    assert Env(tmp_path, scenarios, catalog_file=str(f)).client.get(
        "/api/scenarios", headers=e.h()).json()[0]["available"] is True


def test_full_practice_lifecycle(env):
    r = env.create()
    assert r.status_code == 201 and r.json()["state"] in ("REQUESTED", "PROVISIONING")
    sid = r.json()["id"]
    s = env.wait(sid, "ACTIVE")
    assert s["owner"] == "alice" and s["type"] == "practice" and s["reset"] == "api"
    assert s["task"]["title"].startswith("Test scenario") and "`t-" in s["task"]["text_md"]
    assert s["task"]["difficulty"] == 2 and s["task"]["domain"] == "troubleshooting"
    assert {"name": "base", "role": "base"} in s["targets"]
    assert s["attempt"] == 1 and s["hints_used"] == 0 and s["last_check"] is None
    sb, params = env.sandbox(sid)
    assert sb.setup_calls[0][1]["KOPS_P_NS"] == params["ns"] and "KOPS_FIXTURES" in sb.setup_calls[0][1]
    # failing check
    ck = env.client.post(f"/api/sessions/{sid}/check", json={"wait": False}, headers=env.h()).json()
    assert ck["outcome"] == "FAIL" and ck["required_total"] == 2 and ck["required_passed"] == 1
    assert {c["id"]: c["status"] for c in ck["criteria"]} == {"goal_cm": "fail", "guard_cm": "pass"}
    assert set(ck["criteria"][0]) == {"id", "required", "status", "evidence"}
    assert ck["checked_at"].endswith("Z") and isinstance(ck["seconds"], float)
    assert env.get(sid)["state"] == "ACTIVE" and env.get(sid)["last_check"]["outcome"] == "FAIL"
    # solve and pass
    env.solve(sid)
    ck = env.client.post(f"/api/sessions/{sid}/check", headers=env.h()).json()
    assert ck["outcome"] == "PASS" and ck["required_passed"] == 2
    # a persisted check row with criteria
    from kops.platform.db import CheckRow
    with env.service.db.session() as db:
        rows = db.query(CheckRow).filter_by(session_id=sid).all()
    assert [r.outcome for r in rows] == ["FAIL", "PASS"] and json.loads(rows[0].criteria_json)
    # delete
    assert env.client.delete(f"/api/sessions/{sid}", headers=env.h()).status_code == 202
    env.wait(sid, "DESTROYED")
    assert not env.provider.sandboxes


def test_verifier_error_gives_invalid_outcome(env):
    s = env.active()
    sb, _ = env.sandbox(s["id"])
    import subprocess
    sb.hooks.append(lambda a, i: subprocess.CompletedProcess(a, 1, "", "boom"))
    ck = env.client.post(f"/api/sessions/{s['id']}/check", headers=env.h()).json()
    assert ck["outcome"] == "INVALID" and any(c["status"] == "error" for c in ck["criteria"])
    assert env.get(s["id"])["state"] == "ACTIVE"


def test_check_requires_active_and_practice(env):
    sid = env.create().json()["id"]
    pg = env.client.post("/api/sessions", json={"type": "playground"}, headers=env.h("bob")).json()
    env.wait(pg["id"], "ACTIVE", "bob")
    r = env.client.post(f"/api/sessions/{pg['id']}/check", headers=env.h("bob"))
    assert r.status_code == 409 and r.json()["error"] == "bad_state"
    assert env.get(pg["id"], "bob")["task"] is None
    env.wait(sid, "ACTIVE")


def test_ownership_isolation(env):
    sid = env.active("alice")["id"]
    bob = env.h("bob")
    assert env.client.get("/api/sessions", headers=bob).json() == []
    for method, path in [("get", ""), ("post", "/check"), ("get", "/hints/1"), ("post", "/solution"),
                         ("post", "/restart"), ("post", "/extend"), ("delete", ""), ("get", "/events")]:
        r = getattr(env.client, method)(f"/api/sessions/{sid}{path}", headers=bob)
        assert r.status_code == 404 and r.json()["error"] == "not_found", path
    assert env.get(sid)["state"] == "ACTIVE"
    # admin can see it
    assert env.client.get(f"/api/sessions/{sid}", headers=env.h("root", True)).status_code == 200


def test_quota_409_and_capacity_503(env):
    env.active("alice")
    r = env.create("alice", "t-vm-001")
    assert r.status_code == 409 and r.json()["error"] == "quota_exceeded"
    env.provider.max_sessions = 1
    r = env.create("bob")
    assert r.status_code == 503 and r.json()["error"] == "capacity_exceeded"
    env.provider.max_sessions = 4
    assert env.create("bob").status_code == 201


def test_quota_frees_after_delete(env):
    sid = env.active()["id"]
    env.client.delete(f"/api/sessions/{sid}", headers=env.h())
    assert env.create("alice").status_code == 201


def test_invalid_request(env):
    h = env.h()
    assert env.client.post("/api/sessions", json={"type": "exam"}, headers=h).status_code == 422
    r = env.client.post("/api/sessions", json={"type": "practice", "scenario_id": "zz"}, headers=h)
    assert r.status_code == 422 and r.json()["error"] == "invalid_request"
    assert env.client.post("/api/sessions", json={"type": "practice"}, headers=h).status_code == 422


def test_provision_failure_is_invalid_and_cleans_up(env):
    env.provider.fail_provision = "no vm for you"
    sid = env.create().json()["id"]
    s = env.wait(sid, "INVALID")
    assert "no vm for you" in s["message"]
    assert env.create().status_code == 201     # INVALID does not hold the quota


def test_setup_confirm_failure_is_invalid(env):
    env.provider.setup_hook = lambda sb, sc, e: (setup_hook_fixed(sb, e))

    def setup_hook_fixed(sb, e):
        sb.put("configmap", "keep", e["KOPS_P_NS"])
        sb.put("configmap", "fixed", e["KOPS_P_NS"])   # goal already satisfied: negative control fails
    sid = env.create().json()["id"]
    s = env.wait(sid, "INVALID")
    assert "setup_confirm_failed" in s["message"]
    assert not env.provider.sandboxes          # destroyed


def test_hints(env):
    sid = env.active()["id"]
    h = env.h()
    r = env.client.get(f"/api/sessions/{sid}/hints/1", headers=h).json()
    assert r["n"] == 1 and r["text_md"].startswith("hint 1 for t-")
    env.client.get(f"/api/sessions/{sid}/hints/1", headers=h)
    assert env.get(sid)["hints_used"] == 1            # counted once
    env.client.get(f"/api/sessions/{sid}/hints/3", headers=h)
    assert env.get(sid)["hints_used"] == 2
    assert env.client.get(f"/api/sessions/{sid}/hints/4", headers=h).status_code == 404
    assert env.client.get(f"/api/sessions/{sid}/hints/0", headers=h).status_code == 404


def test_missing_hints_and_explanation(env):
    sid = env.active(scenario="t-api-b-001")["id"]
    assert env.client.get(f"/api/sessions/{sid}/hints/1", headers=env.h()).status_code == 404
    sol = env.client.post(f"/api/sessions/{sid}/solution", headers=env.h()).json()
    assert "No written explanation" in sol["explanation_md"]


def test_solution_marks_assisted_and_progress(env):
    h = env.h()
    prog = lambda: env.client.get("/api/progress", headers=h).json()  # noqa: E731
    status = lambda: {s["id"]: s["status"] for s in env.client.get("/api/scenarios", headers=h).json()}["t-api-a-001"]  # noqa: E731
    sid = env.active()["id"]
    assert status() == "none" and prog()["scenarios"] == []
    env.client.post(f"/api/sessions/{sid}/check", headers=h)
    assert status() == "attempted"
    assert prog()["scenarios"][0]["best_outcome"] == "FAIL"
    sol = env.client.post(f"/api/sessions/{sid}/solution", headers=h).json()
    assert "Create `fixed` in t-" in sol["explanation_md"]
    assert env.get(sid)["solution_viewed"] is True
    assert status() == "attempted"                     # not yet finished or passed
    env.solve(sid)
    env.client.post(f"/api/sessions/{sid}/check", headers=h)
    assert status() == "solved_assisted"
    p = prog()
    assert p["scenarios"][0]["best_outcome"] == "PASS" and p["scenarios"][0]["attempts"] == 1
    assert p["summary"]["cka"]["troubleshooting"] == {"solved": 0, "assisted": 1, "attempted": 0, "total": 3}
    assert p["summary"]["ckad"]["services-networking"]["total"] == 1


def test_progress_solved_and_finished_assisted(env):
    h = env.h()
    st = lambda: {s["id"]: s["status"] for s in env.client.get("/api/scenarios", headers=h).json()}  # noqa: E731
    a = env.active()["id"]
    env.solve(a)
    env.client.post(f"/api/sessions/{a}/check", headers=h)
    assert st()["t-api-a-001"] == "solved"
    # hints do not change status
    env.client.get(f"/api/sessions/{a}/hints/1", headers=h)
    assert st()["t-api-a-001"] == "solved"
    # view the solution then move on without passing: finished attempt after solution = assisted
    env.client.post(f"/api/sessions/{a}/next", json={"scenario_id": "t-vm-001"}, headers=h)
    env.wait(a, "ACTIVE")
    env.client.post(f"/api/sessions/{a}/solution", headers=h)
    env.client.delete(f"/api/sessions/{a}", headers=h)
    env.wait(a, "DESTROYED")
    assert st()["t-vm-001"] == "solved_assisted"


def test_next_api_path_and_restart(env):
    h = env.h()
    sid = env.active()["id"]
    sb, params = env.sandbox(sid)
    env.solve(sid)
    sb.put("namespace", "scratch")
    r = env.client.post(f"/api/sessions/{sid}/next", json={"scenario_id": "t-api-b-001"}, headers=h)
    assert r.status_code == 200 and r.json()["state"] == "RESETTING"
    s = env.wait(sid, "ACTIVE")
    assert s["scenario_id"] == "t-api-b-001" and s["attempt"] == 2 and s["hints_used"] == 0
    assert env.provider.recreated == []                # api reset, no recreation
    sb2, params2 = env.sandbox(sid)
    assert sb2 is sb and not sb.has("namespace", "scratch") and not sb.has("namespace", params["ns"])
    assert sb.has("namespace", params2["ns"])
    # restart: same scenario and params, clean state
    env.solve(sid)
    r = env.client.post(f"/api/sessions/{sid}/restart", headers=h)
    assert r.json()["state"] == "RESETTING"
    s = env.wait(sid, "ACTIVE")
    assert s["attempt"] == 3 and s["scenario_id"] == "t-api-b-001"
    assert env.sandbox(sid)[1] == params2 and not sb.has("configmap", "fixed", params2["ns"])
    assert env.provider.recreated == []


def test_next_vm_path(env):
    h = env.h()
    sid = env.active()["id"]
    r = env.client.post(f"/api/sessions/{sid}/next", json={"scenario_id": "t-vm-001"}, headers=h)
    assert r.status_code == 200
    s = env.wait(sid, "ACTIVE")
    assert s["scenario_id"] == "t-vm-001" and s["reset"] == "vm"
    assert len(env.provider.recreated) == 1
    # vm scenario -> api scenario also recreates (the old one was not api)
    env.client.post(f"/api/sessions/{sid}/next", json={"scenario_id": "t-api-a-001"}, headers=h)
    env.wait(sid, "ACTIVE")
    assert len(env.provider.recreated) == 2
    # now both api: no further recreation
    env.client.post(f"/api/sessions/{sid}/restart", headers=h)
    env.wait(sid, "ACTIVE")
    assert len(env.provider.recreated) == 2
    # restart of a vm scenario recreates
    env.client.post(f"/api/sessions/{sid}/next", json={"scenario_id": "t-vm-001"}, headers=h)
    env.wait(sid, "ACTIVE")
    env.client.post(f"/api/sessions/{sid}/restart", headers=h)
    env.wait(sid, "ACTIVE")
    assert len(env.provider.recreated) == 4


def test_api_reset_failure_falls_back_to_recreate(env):
    h = env.h()
    sid = env.active()["id"]
    sb, _ = env.sandbox(sid)
    import subprocess
    sb.hooks.append(lambda a, i: subprocess.CompletedProcess(a, 1, "", "denied") if a[0] == "delete" else None)
    sb.put("namespace", "stuck")
    env.client.post(f"/api/sessions/{sid}/restart", headers=h)
    env.wait(sid, "ACTIVE")
    assert env.provider.recreated == [sb.id]


def test_next_requires_active(env):
    sid = env.create().json()["id"]
    r = env.client.post(f"/api/sessions/{sid}/next", json={"scenario_id": "t-vm-001"}, headers=env.h())
    assert r.status_code in (200, 409)
    env.wait(sid, "ACTIVE")
    r = env.client.post(f"/api/sessions/{sid}/next", json={"scenario_id": "nope"}, headers=env.h())
    assert r.status_code == 422


def test_reset_failure_is_invalid(env):
    sid = env.active()["id"]
    env.provider.fail_recreate = "disk gone"
    env.client.post(f"/api/sessions/{sid}/next", json={"scenario_id": "t-vm-001"}, headers=env.h())
    s = env.wait(sid, "INVALID")
    assert "disk gone" in s["message"]


def test_extend_limits(env):
    sid = env.active()["id"]
    h = env.h()
    before = env.get(sid)["expires_at"]
    r = env.client.post(f"/api/sessions/{sid}/extend", headers=h)
    assert r.status_code == 200 and r.json()["extensions"] == 1 and r.json()["expires_at"] > before
    assert env.client.post(f"/api/sessions/{sid}/extend", headers=h).json()["extensions"] == 2
    r = env.client.post(f"/api/sessions/{sid}/extend", headers=h)
    assert r.status_code == 409 and r.json()["error"] == "quota_exceeded"


def sse_parse(lines):
    events, ev = [], None
    for line in lines:
        if line.startswith("event:"):
            ev = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            events.append((ev, json.loads(line[5:])))
    return events


def test_sse_replay_after_destroy(env):
    # TestClient buffers a response until the app finishes, so only finite streams work here.
    sid = env.active()["id"]
    env.client.delete(f"/api/sessions/{sid}", headers=env.h())
    env.wait(sid, "DESTROYED")
    with env.client.stream("GET", f"/api/sessions/{sid}/events", headers=env.h()) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        events = sse_parse(list(r.iter_lines()))
    logs = [d for e, d in events if e == "log"]
    assert any("sandbox" in x["line"] for x in logs) and logs[0]["ts"].endswith("Z")
    assert any(x["line"] == "ready" for x in logs)
    states = [d for e, d in events if e == "state"]
    assert states[-1]["state"] == "DESTROYED" and states[-1]["id"] == sid


def test_sse_live_with_real_server(env):
    import socket
    import threading

    import httpx
    import uvicorn
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        port = so.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(env.app, host="127.0.0.1", port=port, log_level="error"))
    t = threading.Thread(target=srv.run, daemon=True)
    t.start()
    try:
        end = time.time() + 5
        while not srv.started and time.time() < end:
            time.sleep(0.02)
        base = f"http://127.0.0.1:{port}"
        sid = httpx.post(f"{base}/api/sessions", json={"type": "practice", "scenario_id": "t-vm-001"},
                         headers=env.h()).json()["id"]
        seen = []
        with httpx.stream("GET", f"{base}/api/sessions/{sid}/events", headers=env.h(), timeout=10) as r:
            for line in r.iter_lines():
                seen.append(line)
                if '"state": "ACTIVE"' in line:
                    break
        events = sse_parse(seen)
        assert [d["state"] for e, d in events if e == "state"][-1] == "ACTIVE"
        assert any(e == "log" for e, _ in events)
        httpx.delete(f"{base}/api/sessions/{sid}", headers=env.h())
        with httpx.stream("GET", f"{base}/api/sessions/{sid}/events", headers=env.h(), timeout=10) as r:
            assert '"state": "DESTROYED"' in "".join(r.iter_lines())     # the stream ends by itself
    finally:
        srv.should_exit = True
        t.join(5)


def test_sse_ends_on_invalid(env):
    env.provider.fail_provision = "boom"
    sid = env.create().json()["id"]
    with env.client.stream("GET", f"/api/sessions/{sid}/events", headers=env.h()) as r:
        body = "\n".join(r.iter_lines())
    assert "INVALID" in body and "boom" in body


def test_sessions_list_order(env):
    a = env.active()["id"]
    env.client.delete(f"/api/sessions/{a}", headers=env.h())
    env.wait(a, "DESTROYED")
    b = env.active()["id"]
    ids = [s["id"] for s in env.client.get("/api/sessions", headers=env.h()).json()]
    assert ids == [b, a]


def test_admin_endpoints(env):
    env.active("alice")
    adm, usr = env.h("root", True), env.h("alice")
    for p in ("/api/admin/sessions", "/api/admin/users", "/api/admin/capacity"):
        r = env.client.get(p, headers=usr)
        assert r.status_code == 403 and r.json()["error"] == "forbidden"
    ss = env.client.get("/api/admin/sessions", headers=adm).json()
    assert len(ss) == 1 and ss[0]["owner"] == "alice"
    users = {u["username"]: u for u in env.client.get("/api/admin/users", headers=adm).json()}
    assert users["alice"]["active_session"] == ss[0]["id"] and users["alice"]["sessions_total"] == 1
    cap = env.client.get("/api/admin/capacity", headers=adm).json()
    assert cap["provider"] == "fake" and cap["active_sessions"] == 1 and cap["orphans"] == 0
    assert cap["nodes"][0]["name"] == "fake-node-1"
    env.provider.add_orphan()
    assert env.client.get("/api/admin/capacity", headers=adm).json()["orphans"] == 1
    assert env.client.delete(f"/api/admin/sessions/{ss[0]['id']}", headers=usr).status_code == 403
    assert env.client.delete(f"/api/admin/sessions/{ss[0]['id']}", headers=adm).status_code == 202
    env.wait(ss[0]["id"], "DESTROYED", "alice")


def test_no_reference_content_leaks(env):
    s = env.active()
    blob = json.dumps(s) + json.dumps(env.client.get("/api/scenarios", headers=env.h()).json())
    for word in ("kubeconfig", "solution.sh", "criteria", "goal_cm", "fixed"):
        assert word not in blob
    assert "baselines" not in blob and "sandbox_id" not in blob


def test_errors_are_json(env):
    r = env.client.get("/api/nope", headers=env.h())
    assert r.status_code == 404 and r.json()["error"] == "not_found"


def test_restart_recovery(env, tmp_path, scenarios):
    """A second app on the same database re-attaches active sessions and fails transient ones."""
    from conftest import Env
    sid = env.active()["id"]
    env.service.update(sid, state="CHECKING")
    stuck = env.client.post("/api/sessions", json={"type": "playground"}, headers=env.h("bob")).json()["id"]
    env.wait(stuck, "ACTIVE", "bob")
    env.service.update(stuck, state="SETUP")
    app2 = type(env.app)  # noqa: F841
    from kops.platform import create_app
    from fastapi.testclient import TestClient
    app = create_app(env.settings, env.provider)
    with TestClient(app) as c2:
        a = c2.get(f"/api/sessions/{sid}", headers=env.h()).json()
        b = c2.get(f"/api/sessions/{stuck}", headers=env.h("bob")).json()
        assert a["state"] == "ACTIVE" and a["targets"]
        assert b["state"] == "INVALID" and "restarted" in b["message"]
        # the re-attached session still verifies with its persisted baselines
        env.solve(sid)
        assert c2.post(f"/api/sessions/{sid}/check", headers=env.h()).json()["outcome"] == "PASS"
