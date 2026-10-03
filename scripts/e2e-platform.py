#!/usr/bin/env python3
"""End-to-end check of a deployed platform through the same path a browser uses.

  PLATFORM=http://192.168.28.124:30800 AUTH=http://192.168.28.124:30880 KC_ADMIN_PASSWORD=... scripts/e2e-platform.py [scenario-id]

It creates a throwaway Keycloak user, logs in with the OIDC authorization-code flow, starts a practice session,
solves the task by typing commands into the terminal WebSocket, checks, reads a hint and the solution, looks at the
progress, deletes the session and the user. Needs: httpx, websockets.
"""
import asyncio, html, json, os, re, sys, time, uuid
import httpx, websockets

PLATFORM = os.environ.get("PLATFORM", "http://192.168.28.124:30800").rstrip("/")
AUTH = os.environ.get("AUTH", "http://192.168.28.124:30880").rstrip("/")
KC_PW = os.environ["KC_ADMIN_PASSWORD"]
SCENARIO = sys.argv[1] if len(sys.argv) > 1 else "kops-net-service-endpoint-repair-001"
USER, PW = "e2e-" + uuid.uuid4().hex[:6], "E2e-" + uuid.uuid4().hex[:10] + "!"
ok = True
SESSION = {"client": None, "id": None}


def step(name, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)
    return cond


def kc_admin() -> httpx.Client:
    c = httpx.Client(base_url=AUTH, timeout=30)
    t = c.post("/realms/master/protocol/openid-connect/token", data={
        "grant_type": "password", "client_id": "admin-cli", "username": "kcadmin", "password": KC_PW}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {t}"
    return c


def create_user(kc) -> str:
    r = kc.post("/admin/realms/kops/users", json={"username": USER, "email": f"{USER}@example.test", "enabled": True,
                "emailVerified": True, "firstName": "E2E", "lastName": "Test",
                "credentials": [{"type": "password", "value": PW, "temporary": False}]})
    assert r.status_code == 201, r.text
    return r.headers["Location"].rsplit("/", 1)[-1]


def login() -> httpx.Client:
    c = httpx.Client(base_url=PLATFORM, timeout=180, follow_redirects=False)
    r = c.get("/auth/login"); assert r.status_code in (302, 307), r.status_code
    kc = httpx.Client(timeout=30, follow_redirects=True)           # a separate cookie jar for Keycloak
    page = kc.get(r.headers["location"])
    action = html.unescape(re.search(r'<form[^>]+id="kc-form-login"[^>]+action="([^"]+)"', page.text).group(1))
    r2 = kc.post(action, data={"username": USER, "password": PW, "credentialId": ""}, follow_redirects=False)
    assert r2.status_code == 302, f"login form returned {r2.status_code}"
    cb = httpx.URL(r2.headers["location"])
    r3 = c.get(f"/auth/callback?{cb.query.decode()}"); assert r3.status_code in (302, 307), r3.status_code
    return c


async def terminal(c: httpx.Client, sid: str, target: str, lines: list[str], settle=2.5) -> str:
    cookie = "; ".join(f"{k}={v}" for k, v in c.cookies.items())
    url = PLATFORM.replace("http", "ws") + f"/api/sessions/{sid}/terminal?target={target}&tab=1"
    out = ""
    async with websockets.connect(url, additional_headers={"Cookie": cookie}, open_timeout=30) as ws:
        async def drain(t):
            nonlocal out
            end = time.time() + t
            while time.time() < end:
                try:
                    m = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5))
                    if m.get("t") == "o": out += m["d"]
                except asyncio.TimeoutError:
                    pass
                except websockets.exceptions.ConnectionClosed:   # the shell exited: normal after `exit`
                    return
        await ws.send(json.dumps({"t": "r", "c": 200, "r": 40}))
        await drain(6)
        for l in lines:
            try:
                await ws.send(json.dumps({"t": "i", "d": l + "\n"}))
            except websockets.exceptions.ConnectionClosed:
                break
            await drain(settle)
        try:
            await ws.send(json.dumps({"t": "i", "d": "exit\n"})); await drain(1.5)
        except websockets.exceptions.ConnectionClosed:
            pass
    return out


def main():
    kc = kc_admin(); uid = create_user(kc)
    try:
        probe = httpx.Client(base_url=PLATFORM, timeout=30, follow_redirects=False)
        reg = probe.get("/auth/login").headers["location"].replace("/protocol/openid-connect/auth", "/protocol/openid-connect/registrations")
        rp = httpx.get(reg, follow_redirects=True, timeout=30)
        step("self-registration page is served", rp.status_code == 200 and "kc-register-form" in rp.text)
        c = login()
        me = c.get("/api/me"); step("OIDC login, /api/me", me.status_code == 200 and me.json()["username"] == USER, me.text[:80])
        cfg = c.get("/api/config").json(); step("config", cfg["provider"] == "kubevirt", json.dumps(cfg["quotas"]))
        sc = {s["id"]: s for s in c.get("/api/scenarios").json()}
        step("scenario is in the catalogue and available", SCENARIO in sc and sc[SCENARIO]["available"])
        r = c.post("/api/sessions", json={"type": "practice", "scenario_id": SCENARIO})
        step("session created", r.status_code == 201, r.text[:100]); s = r.json(); sid = s["id"]
        SESSION.update(client=c, id=sid)
        r2 = c.post("/api/sessions", json={"type": "playground"}); step("second session refused by quota", r2.status_code == 409, r2.text[:80])
        t0 = time.time(); state = s["state"]
        while state not in ("ACTIVE", "INVALID", "DESTROYED") and time.time() - t0 < 600:
            time.sleep(5); s = c.get(f"/api/sessions/{sid}").json(); state = s["state"]
        step(f"session ACTIVE after {int(time.time() - t0)}s", state == "ACTIVE", s.get("message") or state)
        if state != "ACTIVE": return
        task = s["task"]["text_md"]; print("--- task text ---\n" + task + "\n-----------------")
        ns = re.search(r"namespace `([^`]+)`", task).group(1); app = re.search(r"The `([^`]+)` application", task).group(1)
        step("targets listed", [t["name"] for t in s["targets"]][:2] == ["base", "cp-1"], json.dumps(s["targets"]))
        chk = c.post(f"/api/sessions/{sid}/check", json={"wait": False}).json()
        step("CHECK before the fix fails", chk["outcome"] == "FAIL", f"{chk['required_passed']}/{chk['required_total']}")
        out = asyncio.run(terminal(c, sid, "base", ["whoami; hostname; alias k; ssh cp-1 hostname"]))
        step("terminal: base shell and ssh hop to cp-1", "ubuntu" in out and "cp-1" in out, re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", out)[-160:].replace("\n", " | "))
        port = c.get(f"/api/sessions/{sid}").json()  # port is discovered from the cluster by the candidate, as a person would
        out = asyncio.run(terminal(c, sid, "cp-1", [
            f"kubectl -n {ns} get pods -o wide --show-labels | head -3",
            f"P=$(kubectl -n {ns} get deploy {app} -o jsonpath='{{.spec.template.spec.containers[0].ports[0].containerPort}}'); echo port=$P",
            f"kubectl -n {ns} patch service {app} --type merge -p \"{{\\\"spec\\\":{{\\\"selector\\\":{{\\\"app\\\":\\\"{app}\\\",\\\"tier\\\":\\\"web\\\"}},\\\"ports\\\":[{{\\\"port\\\":80,\\\"targetPort\\\":$P}}]}}}}\"",
            f"kubectl -n {ns} get endpointslices"], settle=4))
        clean = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", out)
        step("terminal on cp-1: kubectl works and the patch was applied", "patched" in clean, clean[-200:].replace("\n", " | "))
        chk = c.post(f"/api/sessions/{sid}/check", json={"wait": True}).json()
        step("CHECK after the fix passes", chk["outcome"] == "PASS", json.dumps([(x["id"], x["status"]) for x in chk["criteria"]]))
        h = c.get(f"/api/sessions/{sid}/hints/1"); step("hint 1", h.status_code in (200, 404), h.text[:60])
        sol = c.post(f"/api/sessions/{sid}/solution"); step("solution", sol.status_code == 200 and "explanation_md" in sol.json(), sol.text[:60])
        pr = c.get("/api/progress").json(); st = [x for x in pr["scenarios"] if x["scenario_id"] == SCENARIO]
        step("progress recorded: PASS before the solution was viewed stays `solved`", st and st[0]["status"] == "solved" and st[0]["best_outcome"] == "PASS", json.dumps(st))
        r = c.post(f"/api/sessions/{sid}/restart"); step("restart accepted", r.status_code in (200, 202), r.text[:60])
        t1 = time.time()
        while time.time() - t1 < 300:
            s = c.get(f"/api/sessions/{sid}").json()
            if s["state"] in ("ACTIVE", "INVALID"): break
            time.sleep(3)
        step(f"after restart ACTIVE again in {int(time.time() - t1)}s", s["state"] == "ACTIVE", s.get("message") or s["state"])
        chk = c.post(f"/api/sessions/{sid}/check", json={"wait": False}).json()
        step("task is back to the broken initial state", chk["outcome"] == "FAIL")
        r = c.delete(f"/api/sessions/{sid}"); step("delete accepted", r.status_code in (200, 202, 204))
        time.sleep(30)
        step("session gone from the active list", all(x["state"] in ("DESTROYED", "ENDED") for x in c.get("/api/sessions").json() if x["id"] == sid))
    finally:
        try:
            if SESSION["id"]:
                SESSION["client"].delete(f"/api/sessions/{SESSION['id']}")
        except Exception:
            pass
        kc.delete(f"/admin/realms/kops/users/{uid}")
    print("\nE2E " + ("PASSED" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


main()
