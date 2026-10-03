"""Warm pool: idle single-node clusters that practice sessions take instead of provisioning."""
import subprocess
import time

from conftest import Env


def until(cond, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


def pooled(tmp_path, scenarios, size=1):
    e = Env(tmp_path, scenarios, warm_pool_size=size)
    e.service.refill()
    assert until(lambda: e.service.pool_status()["ready"] == size)
    return e


def test_pool_fills_up_to_its_target_and_the_sweeper_leaves_it_alone(tmp_path, scenarios):
    e = pooled(tmp_path, scenarios, size=2)
    assert len(e.provider.sandboxes) == 2
    assert e.service.sweep()["orphans"] == 0
    assert len(e.provider.sandboxes) == 2


def test_practice_session_takes_a_warm_sandbox_and_the_pool_refills(tmp_path, scenarios):
    e = pooled(tmp_path, scenarios)
    warm_id = next(iter(e.provider.sandboxes))
    sid = e.create().json()["id"]
    s = e.wait(sid, "ACTIVE")
    sb, _ = e.sandbox(sid)
    assert sb.id == warm_id and sb.session_id == sid          # the pre-built cluster, now the session's own
    with e.service.db.session() as db:
        from kops.platform.db import SessionEvent
        lines = [x.line for x in db.query(SessionEvent).filter_by(session_id=sid)]
    assert "using a pre-provisioned cluster" in lines and "provisioning sandbox" not in lines
    assert until(lambda: e.service.pool_status()["ready"] == 1)    # a new warm sandbox replaced it
    assert e.provider._n == 2 and s["state"] == "ACTIVE"


def test_unhealthy_warm_sandbox_is_replaced_by_a_fresh_one(tmp_path, scenarios):
    e = pooled(tmp_path, scenarios)
    warm = next(iter(e.provider.sandboxes.values()))
    warm.hooks.append(lambda a, i: subprocess.CompletedProcess(a, 1, "", "down") if "--raw" in a else None)
    sid = e.create().json()["id"]
    e.wait(sid, "ACTIVE")
    sb, _ = e.sandbox(sid)
    assert sb.id != warm.id and warm.id in e.provider.destroyed


def test_multi_worker_and_playground_do_not_use_the_pool(tmp_path, scenarios):
    e = pooled(tmp_path, scenarios)
    warm_id = next(iter(e.provider.sandboxes))
    sid = e.client.post("/api/sessions", json={"type": "playground"}, headers=e.h()).json()["id"]
    e.wait(sid, "ACTIVE")
    sb, _ = e.sandbox(sid)
    assert sb.id != warm_id and warm_id in e.provider.sandboxes


def test_idle_pool_sandbox_makes_room_for_a_session_that_cannot_use_it(tmp_path, scenarios):
    e = pooled(tmp_path, scenarios)
    e.provider.max_sessions = 1                                 # the pool sandbox fills the only slot
    r = e.client.post("/api/sessions", json={"type": "playground"}, headers=e.h())
    assert r.status_code == 201
    e.wait(r.json()["id"], "ACTIVE")
    assert e.service.pool_status()["ready"] == 0


def test_pool_is_not_built_beyond_capacity(tmp_path, scenarios):
    e = Env(tmp_path, scenarios, warm_pool_size=3)
    e.provider.max_sessions = 1
    e.service.refill()
    assert until(lambda: e.service.pool_status()["ready"] == 1)
    time.sleep(0.2)
    assert len(e.provider.sandboxes) == 1


def test_restart_recovers_idle_sandboxes_and_drops_half_built_ones(tmp_path, scenarios):
    e = pooled(tmp_path, scenarios)
    half = e.provider.provision(__import__("kops.providers.base", fromlist=["SandboxSpec"]).SandboxSpec(
        session_id="pool-half", owner="pool"), lambda _: None)
    e.service._warm.clear()
    e.service.recover()
    assert e.service.pool_status()["ready"] == 1
    assert half.id in e.provider.destroyed
