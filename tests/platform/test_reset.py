import json

from kops.providers.fake import FakeSandbox
from kops.reset import Baseline, Reset, declared_reset


def cluster() -> FakeSandbox:
    sb = FakeSandbox("c", "s_x")
    sb.put("namespace", "default")
    sb.put("namespace", "kube-system")
    sb.put("configmap", "coredns", "kube-system", data={"Corefile": "ok"})
    sb.put("configmap", "kube-root-ca.crt", "default", data={"ca": "1"})
    sb.put("namespace", "keep-ns")
    sb.put("configmap", "base-cm", "keep-ns", data={"a": "b"})
    return sb


def dirty(sb: FakeSandbox) -> None:
    sb.put("namespace", "q1")
    sb.put("deployment", "web", "q1", spec={"replicas": 2})
    sb.put("service", "web", "q1")
    sb.put("clusterrole", "tmp")
    sb.put("configmap", "extra", "keep-ns")                        # extra object in a kept namespace
    sb.put("configmap", "coredns", "kube-system", data={"Corefile": "tampered"})   # changed
    del sb.objects[("configmap", "keep-ns", "base-cm")]            # removed


def test_digest_stable_and_sensitive():
    sb = cluster()
    r = Reset(sb)
    base = r.capture_baseline()
    assert r.digest() == base.digest
    sb.put("configmap", "root-ca-noise", "default")
    assert r.digest() != base.digest


def test_ignored_and_status_metadata_do_not_count():
    sb = cluster()
    r = Reset(sb)
    base = r.capture_baseline()
    sb.objects[("configmap", "kube-system", "coredns")]["metadata"]["resourceVersion"] = "999"
    sb.objects[("configmap", "kube-system", "coredns")]["status"] = {"x": 1}
    sb.put("configmap", "kube-root-ca.crt", "keep-ns")
    assert r.digest() == base.digest


def test_reset_restores_baseline():
    sb = cluster()
    r = Reset(sb)
    base = r.capture_baseline()
    dirty(sb)
    assert r.digest() != base.digest
    rep = r.reset(base)
    assert rep.deleted >= 3 and rep.restored == 2 and not rep.errors
    assert r.digest() == base.digest
    assert not sb.has("namespace", "q1") and not sb.has("deployment", "web", "q1")
    assert sb.objects[("configmap", "kube-system", "coredns")]["data"]["Corefile"] == "ok"


def test_wait_restored_true_and_false():
    sb = cluster()
    r = Reset(sb)
    base = r.capture_baseline()
    dirty(sb)
    assert r.wait_restored(base, timeout=2, interval=0.01)
    # a cluster that refuses deletes never converges
    dirty(sb)
    sb.hooks.append(lambda a, i: __import__("subprocess").CompletedProcess(a, 1, "", "denied") if a[0] == "delete" else None)
    assert not r.wait_restored(base, timeout=0.2, interval=0.01)


def test_baseline_json_roundtrip():
    sb = cluster()
    base = Reset(sb).capture_baseline()
    again = Baseline.from_json(base.to_json())
    assert again.digest == base.digest and again.objects == base.objects
    json.loads(base.to_json())


def test_secrets_never_stored():
    sb = cluster()
    sb.put("secret", "tok", "keep-ns", data={"password": "hunter2"})
    r = Reset(sb)
    base = r.capture_baseline()
    assert "hunter2" not in base.to_json()
    sb.put("secret", "new", "keep-ns", data={"x": "y"})     # created: deleted again
    r.reset(base)
    assert not sb.has("secret", "new", "keep-ns")
    del sb.objects[("secret", "keep-ns", "tok")]            # removed: cannot be restored
    assert r.reset(base).errors


def test_configurable_kinds():
    sb = cluster()
    r = Reset(sb, cluster_kinds=["namespaces"], namespaced_kinds=[])
    base = r.capture_baseline()
    sb.put("configmap", "extra", "keep-ns")            # not tracked
    assert r.digest() == base.digest


def test_declared_reset(tmp_path):
    assert declared_reset({}) == "vm"
    assert declared_reset({"reset": "api"}) == "api"
    assert declared_reset({"reset": {"strategy": "destroy-cluster"}}) == "vm"
    assert declared_reset({"reset": {"mode": "api"}}) == "api"
    assert declared_reset({"reset": "bogus"}) == "vm"
    p = tmp_path / "scenario.yaml"
    p.write_text("id: x\nreset: api\ntitle: '{{ns}}'\nparams: {{ns}}\n")
    assert declared_reset(tmp_path) == "api"
