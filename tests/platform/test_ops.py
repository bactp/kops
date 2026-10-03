import json
import time

from kops.platform.db import SessionRow, utcnow
from datetime import timedelta


def test_terminal_websocket_echo(env):
    sid = env.active()["id"]
    with env.client.websocket_connect(f"/api/sessions/{sid}/terminal?target=base&tab=1", headers=env.h()) as ws:
        ws.send_text(json.dumps({"t": "r", "c": 100, "r": 30}))
        ws.send_text(json.dumps({"t": "i", "d": "echo hello-$((1+2)); stty size\n"}))
        buf = ""
        while "hello-3" not in buf or "30 100" not in buf:
            m = json.loads(ws.receive_text())
            assert m["t"] == "o"
            buf += m["d"]
        ws.send_text(json.dumps({"t": "i", "d": "exit 3\n"}))
        while True:
            m = json.loads(ws.receive_text())
            if m["t"] == "x":
                assert m["code"] == 3
                break


def test_terminal_scrubs_environment(env, monkeypatch):
    monkeypatch.setenv("KOPS_SESSION_SECRET", "topsecret")
    sid = env.active()["id"]
    with env.client.websocket_connect(f"/api/sessions/{sid}/terminal", headers=env.h()) as ws:
        ws.send_text(json.dumps({"t": "i", "d": "echo S=[${KOPS_SESSION_SECRET}]\n"}))
        buf = ""
        while "S=[]" not in buf:
            buf += json.loads(ws.receive_text())["d"]
        assert "topsecret" not in buf


def test_terminal_closes_child_on_disconnect(env):
    import subprocess
    sid = env.active()["id"]
    marker = "sleep 31337"
    with env.client.websocket_connect(f"/api/sessions/{sid}/terminal", headers=env.h()) as ws:
        ws.send_text(json.dumps({"t": "i", "d": f"{marker} &\n echo up\n"}))
        buf = ""
        while "up" not in buf.replace("echo up", ""):
            buf += json.loads(ws.receive_text())["d"]
    time.sleep(0.5)
    left = subprocess.run(["pgrep", "-f", marker], capture_output=True, text=True).stdout.strip()
    assert left == ""


def test_terminal_access_control(env):
    from starlette.websockets import WebSocketDisconnect
    import pytest
    sid = env.active("alice")["id"]
    for headers, code in [({}, 4401), (env.h("bob"), 4404)]:
        with pytest.raises(WebSocketDisconnect) as e:
            with env.client.websocket_connect(f"/api/sessions/{sid}/terminal", headers=headers):
                pass
        assert e.value.code == code
    with pytest.raises(WebSocketDisconnect):
        with env.client.websocket_connect(f"/api/sessions/{sid}/terminal?target=nope", headers=env.h()):
            pass
    with env.client.websocket_connect(f"/api/sessions/{sid}/terminal", headers=env.h("root", True)):
        pass   # admin may connect


def test_sweeper_destroys_orphans(env):
    sid = env.active()["id"]
    orphan = env.provider.add_orphan("s_unknown")
    ended = env.provider.add_orphan(sid.replace("s_", "s_"))   # session row exists, sandbox id differs
    res = env.service.sweep()
    assert orphan in env.provider.destroyed and res["orphans"] >= 1
    # a live session's sandbox survives
    assert env.get(sid)["state"] == "ACTIVE" and env.sandbox(sid)[0].id in env.provider.sandboxes
    assert ended in env.provider.destroyed


def test_sweeper_destroys_ended_session_sandbox(env):
    sid = env.active()["id"]
    sb, _ = env.sandbox(sid)
    env.service.update(sid, state="ENDED")
    env.service.sweep()
    assert sb.id in env.provider.destroyed and env.get(sid)["state"] == "DESTROYED"


def test_expiry(env):
    sid = env.active()["id"]
    sb, _ = env.sandbox(sid)
    env.service.update(sid, expires_at=utcnow() - timedelta(seconds=1))
    assert env.service.sweep()["expired"] == 1
    env.wait(sid, "DESTROYED")
    assert sb.id in env.provider.destroyed
    # progress seconds finalised, new session possible
    assert env.create().status_code == 201


def test_background_sweeper_runs(tmp_path, scenarios):
    from conftest import Env
    from fastapi.testclient import TestClient
    e = Env(tmp_path, scenarios)
    e.settings.sweep_interval_seconds = 0.05
    from kops.platform import create_app
    app = create_app(e.settings, e.provider)
    orphan = e.provider.add_orphan("s_zzz")
    with TestClient(app):
        end = time.time() + 5
        while orphan not in e.provider.destroyed and time.time() < end:
            time.sleep(0.05)
    assert orphan in e.provider.destroyed


def test_static_dashboard_mount(tmp_path, scenarios):
    from conftest import Env
    web = tmp_path / "web"
    web.mkdir()
    (web / "index.html").write_text("<h1>kops</h1>")
    e = Env(tmp_path, scenarios)
    e.settings.web_dir = web
    from kops.platform import create_app
    from fastapi.testclient import TestClient
    c = TestClient(create_app(e.settings, e.provider))
    assert "<h1>kops</h1>" in c.get("/").text
    assert c.get("/api/me").status_code == 401           # API still wins over the static mount
    assert c.get("/healthz").json()["status"] == "ok"


def test_readyz_unavailable_when_provider_down(env):
    env.provider.capacity = lambda: (_ for _ in ()).throw(RuntimeError("down"))
    assert env.client.get("/readyz").status_code == 503


def test_oidc_not_configured_and_role_claims(env):
    r = env.client.get("/auth/login", follow_redirects=False)
    assert r.status_code == 502 and r.json()["error"] == "provider_error"
    from kops.platform.auth import role_claims
    import base64
    body = base64.urlsafe_b64encode(json.dumps({"realm_access": {"roles": ["kops-admin"]}}).encode()).decode().rstrip("=")
    assert "kops-admin" in role_claims({"groups": ["g"]}, f"h.{body}.s") and "g" in role_claims({"groups": ["g"]}, None)


def test_admin_from_settings_list(tmp_path, scenarios):
    from conftest import Env
    e = Env(tmp_path, scenarios, admin_users=["boss"])
    from kops.platform.auth import upsert_user
    assert upsert_user(e.service.db, e.settings, "boss").is_admin
    assert not upsert_user(e.service.db, e.settings, "peon").is_admin
    e.settings.oidc_admin_role = "ops"
    assert upsert_user(e.service.db, e.settings, "peon2", roles={"ops"}).is_admin


def test_kind_provider_importable_and_names():
    from kops.providers.kind import KindProvider, cluster_name
    assert cluster_name("s_ab12cd34") == "kops-s-ab12cd34" and KindProvider().name == "kind"


def test_serve_cli_parses():
    from kops.cli import main
    import pytest
    with pytest.raises(SystemExit):
        main(["serve", "--help"])
