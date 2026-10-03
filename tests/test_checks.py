"""Unit tests for the verifier's extended check vocabulary (no cluster needed)."""
import json
import subprocess

import pytest

from kops.verifier import CheckError, FAIL, PASS, Verifier, parse_path, quantity, select


class Fake:
    """kubectl stub: `table` maps the joined args (without '-o json') to (rc, stdout, stderr)."""

    def __init__(self, table):
        self.table, self.calls = table, []

    def kubectl(self, *args, **kw):
        args = list(args)
        key = " ".join(a for a in args if a not in ("-o", "json"))
        self.calls.append(key)
        v = self.table.get(key)
        if v is None:
            return subprocess.CompletedProcess(args, 1, "", "Error from server (NotFound): not found")
        rc, out, err = v if isinstance(v, tuple) else (0, json.dumps(v), "")
        return subprocess.CompletedProcess(args, rc, out, err)


def run(table, **check):
    return Verifier(Fake(table), [{"id": "c", "invariant": "i", "required": True, "check": check}]
                    ).evaluate(settle=False)[0]


POD = {"spec": {"containers": [{"name": "a", "image": "busybox:1.36.1", "resources": {"limits": {"memory": "128Mi"}},
                                 "env": [{"name": "X", "value": "1"}, {"name": "Y", "valueFrom": {"secretKeyRef": {"name": "s"}}}]},
                                {"name": "b", "image": "agnhost"}]},
       "metadata": {"name": "p", "labels": {"app": "w"}},
       "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]}}


def test_path_index_star_filter_and_quoted_keys():
    assert select(POD, ".spec.containers[0].image") == (["busybox:1.36.1"], False)
    assert select(POD, ".spec.containers[*].name") == (["a", "b"], True)
    assert select(POD, '.spec.containers[?(@.name=="b")].image') == (["agnhost"], True)
    assert select(POD, ".spec.containers[0].env[?(@.name==\"Y\")].valueFrom.secretKeyRef.name")[0] == ["s"]
    assert select(POD, ".spec.containers[-1].name")[0] == ["b"]
    assert select({"metadata": {"annotations": {"a.b/c": "v"}}}, ".metadata.annotations['a.b/c']")[0] == ["v"]
    assert select(POD, ".spec.nothing.here") == ([], False)
    with pytest.raises(CheckError):
        parse_path(".spec.containers[?bad]")


def test_quantity_parsing():
    assert quantity("128Mi") == 128 * 2**20 and quantity("500m") == 0.5 and quantity("2") == 2
    with pytest.raises(CheckError):
        quantity("lots")


@pytest.mark.parametrize("path,op,value,expect", [
    (".spec.containers[0].image", "eq", "busybox:1.36.1", PASS),
    (".spec.containers[0].image", "ne", "busybox:1.36.1", FAIL),
    (".spec.containers[*].image", "regex", "busybox|agnhost", PASS),
    (".spec.containers[*].image", "regex", "busybox", FAIL),            # all_items default
    (".spec.containers[0].resources.limits.memory", "qty_gte", "100Mi", PASS),
    (".spec.containers[0].resources.limits.memory", "qty_lte", "100Mi", FAIL),
    (".spec.containers[1].resources", "absent", None, PASS),
    (".spec.containers[0].env[?(@.name==\"X\")].value", "eq", "1", PASS),
    (".spec.containers[0].env[?(@.name==\"Z\")].value", "exists", None, FAIL),
    (".metadata.labels", "subset", {"app": "w"}, PASS),
    (".metadata.labels.app", "in", ["w", "z"], PASS),
])
def test_field_ops(path, op, value, expect):
    r = run({"-n n get pod p": POD}, type="k8s.field", resource={"kind": "Pod", "name": "p", "namespace": "n"},
            jsonpath=path, op=op, value=value)
    assert r.status == expect, r.evidence


def test_field_any_item_and_selector_refs_and_missing():
    t = {"-n n get pod -l app=w": {"items": [POD, {**POD, "metadata": {"name": "q"}, "spec": {"containers": [{"image": "x"}]}}]}}
    c = dict(type="k8s.field", resource={"kind": "Pod", "selector": "app=w", "namespace": "n"},
             jsonpath=".spec.containers[0].image", op="eq", value="x")
    assert run(t, **c).status == FAIL                      # all items must match
    assert run(t, **c, all_items=False).status == PASS
    assert run({"-n n get pod -l app=w": {"items": []}}, **c).status == FAIL   # missing resource is an agent-state FAIL, not ERROR


def test_exists_count_condition():
    t = {"-n n get pod p": POD, "-n n get pod -l app=w": {"items": [POD, POD]}}
    ref = {"kind": "Pod", "name": "p", "namespace": "n"}
    assert run(t, type="k8s.exists", resource=ref, expect="present").status == PASS
    assert run(t, type="k8s.exists", resource={**ref, "name": "zz"}, expect="absent").status == PASS
    assert run(t, type="k8s.exists", resource={**ref, "name": "zz"}, expect="present").status == FAIL
    sel = {"kind": "Pod", "selector": "app=w", "namespace": "n"}
    assert run(t, type="k8s.count", resource=sel, op="eq", value=2).status == PASS
    assert run(t, type="k8s.count", resource=sel, op="gte", value=3).status == FAIL
    assert run(t, type="k8s.count", resource=sel, op="eq", value=2, field_filter=".status.phase==Running").status == PASS
    assert run(t, type="k8s.count", resource=sel, op="eq", value=0, field_filter=".status.phase!=Running").status == PASS
    anno = {"-n n get pod -l app=w": {"items": [{"metadata": {"annotations": {"x/default": "true"}}}, {"metadata": {}}]}}
    assert run(anno, type="k8s.count", resource=sel, op="eq", value=1, field_filter=".metadata.annotations['x/default']==true").status == PASS
    assert run(t, type="k8s.condition", resource=ref, condition="Ready", status="True").status == PASS
    assert run(t, type="k8s.condition", resource=ref, condition="Available", status="True").status == FAIL


def test_can_i_allow_deny_and_infrastructure_error():
    t = {"auth can-i get pods --as=system:serviceaccount:n:sa -n n": (0, "yes\n", ""),
         "auth can-i delete pods --as=system:serviceaccount:n:sa -n n": (1, "no\n", "")}
    base = dict(type="k8s.can_i", **{"as": "system:serviceaccount:n:sa"}, resource="pods", namespace="n")
    assert run(t, verb="get", expect="allow", **base).status == PASS
    assert run(t, verb="delete", expect="deny", **base).status == PASS
    assert run(t, verb="delete", expect="allow", **base).status == FAIL
    assert run({}, verb="get", expect="allow", **base).status == "error"     # unusable answer => INVALID


def test_logs_match_and_no_match():
    t = {"-n n logs deployment/d": (0, "boot\nfatal: X missing\nboot\n", ""),
         "-n n logs deployment/gone": (1, "", "Error from server (BadRequest): container is waiting to start")}
    ref = {"kind": "Deployment", "name": "d", "namespace": "n"}
    assert run(t, type="k8s.logs", resource=ref, regex="fatal: \\w+ missing").status == PASS
    assert run(t, type="k8s.logs", resource=ref, regex="boot", min_matches=3).status == FAIL
    assert run(t, type="k8s.logs", resource=ref, regex="fatal", expect="no_match").status == FAIL
    assert run(t, type="k8s.logs", resource={**ref, "name": "gone"}, regex="x").status == FAIL


def test_placement():
    mk = lambda n, node: {"metadata": {"name": n}, "status": {"phase": "Running"}, "spec": {"nodeName": node}}
    t = {"-n n get pod -l app=w": {"items": [mk("a", "w1"), mk("b", "w1"), mk("c", "w2")]},
         "get node -l pool=x": {"items": [{"metadata": {"name": "w1"}}]}}
    c = dict(type="k8s.placement", namespace="n", selector="app=w")
    assert run(t, **c, min_pods=3).status == PASS
    assert run(t, **c, node_selector="pool=x").status == FAIL             # c is on w2
    assert run(t, **c, node_selector="pool=x", mode="outside").status == FAIL
    assert run(t, **c, max_per_node=1).status == FAIL
    assert run(t, **c, min_distinct_nodes=2).status == PASS


def _exec_key(pod="probe", ns="kops-probe"):
    return f"-n {ns} exec {pod} --"


def test_http_status_body_and_blocked():
    ok = (0, "hello v2", "  HTTP/1.1 200 OK\n  Content-Length: 8\n")
    nf = (1, "", "wget: server returned error: HTTP/1.1 404 Not Found\ncommand terminated with exit code 1")
    to = (1, "", "wget: download timed out\ncommand terminated with exit code 1")
    frm = {"namespace": "kops-probe"}
    k = _exec_key() + " wget -q -S -O - -T 3 http://s/"
    assert run({k: ok}, type="net.http", **{"from": frm}, url="http://s/", expect="reachable", status=200,
               body_regex="v2").status == PASS
    assert run({k: ok}, type="net.http", **{"from": frm}, url="http://s/", expect="reachable", body_regex="v1").status == FAIL
    assert run({k: nf}, type="net.http", **{"from": frm}, url="http://s/", expect="reachable").status == FAIL
    assert run({k: to}, type="net.http", **{"from": frm}, url="http://s/", expect="blocked").status == PASS
    assert run({k: ok}, type="net.http", **{"from": frm}, url="http://s/", expect="blocked").status == FAIL
    gone = {k: (1, "", "Error from server (NotFound): pods \"probe\" not found")}
    assert run(gone, type="net.http", **{"from": frm}, url="http://s/", expect="reachable").status == "error"


def test_http_from_labelled_client_pod():
    pods = {"-n n get pods -l app=cl,role=a": {"items": [{"metadata": {"name": "cl-1"}, "status": {"phase": "Running"}}]}}
    k = "-n n exec cl-1 -- wget -q -S -O - -T 3 http://s/"
    t = {**pods, k: (0, "", "  HTTP/1.1 200 OK")}
    c = dict(type="net.http", **{"from": {"namespace": "n", "labels": {"app": "cl", "role": "a"}}},
             url="http://s/", expect="reachable")
    assert run(t, **c).status == PASS
    empty = {"-n n get pods -l app=cl,role=a": {"items": []}}
    assert run(empty, **c).status == FAIL            # no running client pod: the agent removed it


def test_tcp_and_dns():
    frm = {"namespace": "kops-probe"}
    assert run({_exec_key() + " nc -z -w 3 h 80": (0, "", "")}, type="net.tcp", **{"from": frm}, host="h", port=80,
               expect="reachable").status == PASS
    blocked = {_exec_key() + " nc -z -w 3 h 80": (1, "", "command terminated with exit code 1")}
    assert run(blocked, type="net.tcp", **{"from": frm}, host="h", port=80, expect="blocked").status == PASS
    good = "Server: 10.96.0.10\nAddress: 10.96.0.10:53\n\nName:\tweb.n.svc.cluster.local\nAddress: 10.96.23.36\n"
    bad = "** server can't find x: NXDOMAIN\n"
    k = _exec_key() + " nslookup web.n.svc.cluster.local"
    assert run({k: (0, good, "")}, type="net.dns", **{"from": frm}, name="web.n.svc.cluster.local",
               expect="resolves", answer_regex=r"10\.96\.").status == PASS
    assert run({k: (1, bad, "command terminated with exit code 1")}, type="net.dns", **{"from": frm},
               name="web.n.svc.cluster.local", expect="resolves").status == FAIL
    assert run({k: (1, bad, "command terminated with exit code 1")}, type="net.dns", **{"from": frm},
               name="web.n.svc.cluster.local", expect="nxdomain").status == PASS


def test_stability_requires_every_sample_and_unchanged_uses_paths():
    obj = {"spec": {"x": 1}}
    fk = Fake({"-n n get deployment d": obj})
    inner = dict(type="k8s.field", resource={"kind": "Deployment", "name": "d", "namespace": "n"},
                 jsonpath=".spec.x", op="eq", value=1)
    c = {"id": "s", "invariant": "i", "required": True,
         "check": {"type": "stability", "window_seconds": 5, "samples": 2, "check": inner}}
    import kops.verifier as V
    orig = V.time.sleep
    V.time.sleep = lambda s: obj["spec"].__setitem__("x", 2)       # state flips between samples
    try:
        assert Verifier(fk, [c]).evaluate(settle=False)[0].status == FAIL
    finally:
        V.time.sleep = orig
    obj["spec"]["x"] = 1
    V.time.sleep = lambda s: None
    try:
        assert Verifier(fk, [c]).evaluate(settle=False)[0].status == PASS
    finally:
        V.time.sleep = orig
    g = {"id": "g", "invariant": "i", "required": True,
         "check": {"type": "k8s.unchanged", "resource": inner["resource"], "scope": "spec"}}
    v = Verifier(fk, [g])
    v.capture_baselines()
    assert v.evaluate(settle=False)[0].status == PASS
    obj["spec"]["x"] = 3
    assert v.evaluate(settle=False)[0].status == FAIL


def test_topology_workers_in_kind_config(tmp_path, monkeypatch):
    from kops import backend_kind, config
    monkeypatch.setattr(config, "RUN_DIR", tmp_path)
    seen = {}
    monkeypatch.setattr(backend_kind, "_run", lambda argv, **kw: (seen.setdefault("argv", [str(a) for a in argv]),
                                                                  subprocess.CompletedProcess(argv, 0 if "docker" in str(argv[0]) else 1, "", "stop"))[1])
    c = backend_kind.KindCluster("kops-t1", workers=2)
    with pytest.raises(backend_kind.BackendError):
        c.create()
    cfg = (tmp_path / "kops-t1.kind.yaml").read_text()
    assert cfg.count("role: worker") == 2 and "control-plane" in cfg


# -- lint: content checks ------------------------------------------------------------
def _copy_scenario(tmp_path):
    import shutil
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / "scenarios" / "kops-net-service-endpoint-repair-001"
    dst = tmp_path / "kops-net-service-endpoint-repair-001"
    shutil.copytree(src, dst)
    return dst


def test_lint_content_clean_on_existing_scenario(tmp_path):
    from kops.lint import lint_content
    assert lint_content(_copy_scenario(tmp_path)) == []


def test_lint_content_flags_unknown_param_pipe_forbidden_flag_and_denylist(tmp_path):
    from kops.lint import lint_content
    d = _copy_scenario(tmp_path)
    (d / "fixtures" / "service-broken.yaml").write_text("name: {{nope}}\n")
    (d / "reference" / "solution.sh").write_text(
        "kubectl get pods | grep x\nkubectl auth can-i get pods --as=u\nkubectl get ns/neptune\nls -la\n")
    (d / "task.md").write_text("see killer.sh and -n neptune\n")
    probs = " | ".join(lint_content(d))
    assert "unknown template parameter 'nope'" in probs
    assert "shell syntax" in probs and "forbidden flag" in probs and "not a kubectl command" in probs
    assert "denylist hit in task.md: ks-vendor:killer.sh" in probs and "ks-namespaces:neptune" in probs


def test_lint_content_flags_invalid_rendered_yaml(tmp_path):
    from kops.lint import lint_content
    d = _copy_scenario(tmp_path)
    (d / "fixtures" / "service-broken.yaml").write_text("a: [unclosed\n")
    assert any("invalid YAML" in p for p in lint_content(d))


def test_probe_pod_is_pinned_to_control_plane_when_workers_exist(monkeypatch):
    import json as _json
    from kops import backend_kind
    for workers, pinned in ((0, False), (2, True)):
        c = backend_kind.KindCluster("kops-t2", workers=workers)
        calls = []
        monkeypatch.setattr(c, "kubectl", lambda *a, **kw: calls.append(list(a)) or subprocess.CompletedProcess(a, 0, "", ""))
        c._provision_probe()
        run = next(a for a in calls if "run" in a)
        ov = [x for x in run if x.startswith("--overrides=")]
        assert bool(ov) == pinned
        if pinned:
            spec = _json.loads(ov[0].split("=", 1)[1])["spec"]
            assert spec["nodeSelector"] == {"node-role.kubernetes.io/control-plane": ""}
            assert spec["tolerations"][0]["operator"] == "Exists"


def test_field_value_from_other_object():
    t = {"-n n get configmap cm": {"data": {"podIP": "10.244.1.7"}},
         "-n n get pod -l app=w": {"items": [{"status": {"podIP": "10.244.1.7"}}]}}
    c = dict(type="k8s.field", resource={"kind": "ConfigMap", "name": "cm", "namespace": "n"}, jsonpath=".data.podIP", op="eq",
             value_from={"resource": {"kind": "Pod", "selector": "app=w", "namespace": "n"}, "jsonpath": ".status.podIP"})
    assert run(t, **c).status == PASS
    t["-n n get configmap cm"]["data"]["podIP"] = "10.96.0.9"
    assert run(t, **c).status == FAIL
    t["-n n get pod -l app=w"] = {"items": []}
    assert run(t, **c).status == "error"        # missing reference object is an infrastructure problem
