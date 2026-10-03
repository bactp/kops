import json
import subprocess
from pathlib import Path

from kops.providers.base import SandboxSpec
from kops.providers.kubevirt import (KubeVirtProvider, KubeVirtSettings, cloud_init, label_safe, mem_mib,
                                     namespace_for, network_policies, vm_manifest)


class FakeRunner:
    def __init__(self, responses=None):
        self.calls, self.responses = [], responses or {}

    def run(self, argv, *, input=None, timeout=60, env=None):
        self.calls.append((list(map(str, argv)), input))
        if str(argv[0]).endswith("ssh-keygen"):          # behave like ssh-keygen: create the key pair
            f = Path(argv[argv.index("-f") + 1]); f.write_text("PRIVATE"); Path(str(f) + ".pub").write_text("ssh-ed25519 AAAA test")
        for key, out in self.responses.items():
            if key in " ".join(map(str, argv)):
                return subprocess.CompletedProcess(argv, 0, out, "")
        return subprocess.CompletedProcess(argv, 0, "", "")


def provider(tmp_path, runner, **kw):
    return KubeVirtProvider(KubeVirtSettings(work_dir=tmp_path, **kw), runner)


def test_namespace_and_label_helpers():
    assert namespace_for("s_3F9a1c") == "kops-s-s3f9a1c"
    assert namespace_for("x" * 40).startswith("kops-s-") and len(namespace_for("x" * 40)) <= 19
    assert label_safe("alice@example.com") == "alice_example.com"
    assert mem_mib("3Gi") == 3072 and mem_mib("512Mi") == 512


def test_network_policies_isolate_sessions_and_allow_only_the_platform():
    pols = {p["metadata"]["name"]: p["spec"] for p in network_policies("kops-gw")}
    assert pols["default-deny"]["policyTypes"] == ["Ingress", "Egress"] and "ingress" not in pols["default-deny"]
    base = pols["platform-to-base-ssh"]
    assert base["podSelector"]["matchLabels"] == {"role": "base"}
    assert base["ingress"][0]["ports"] == [{"protocol": "TCP", "port": 22}]
    assert base["ingress"][0]["from"][0]["namespaceSelector"]["matchLabels"] == {"kubernetes.io/metadata.name": "kops-gw"}
    assert [p["port"] for p in pols["platform-to-node"]["ingress"][0]["ports"]] == [6443, 22]
    # egress is limited to the session itself, plus DNS to kube-dns; never the internet or other namespaces
    for name, spec in pols.items():
        for rule in spec.get("egress", []):
            if name == "allow-dns":
                assert rule["to"][0]["podSelector"]["matchLabels"] == {"k8s-app": "kube-dns"}
                assert {p["port"] for p in rule["ports"]} == {53}
            else:
                assert all("podSelector" in t and "namespaceSelector" not in t and "ipBlock" not in t for t in rule["to"])


def test_vm_manifest_uses_containerdisk_and_labels():
    vm = vm_manifest("cp-1", "node", 2, "3Gi", "localhost/kops/node-golden:v3", cloud_init("cp-1", ["ssh-ed25519 AAA"]), "s_1")
    vols = {v["name"]: v for v in vm["spec"]["template"]["spec"]["volumes"]}
    assert vols["root"]["containerDisk"]["image"].endswith("node-golden:v3")
    assert "persistentVolumeClaim" not in vols["root"]
    assert vm["spec"]["template"]["metadata"]["labels"]["role"] == "node"
    assert "hostname: cp-1" in vols["ci"]["cloudInitNoCloud"]["userData"]


def test_destroy_deletes_namespace_and_secret(tmp_path):
    r = FakeRunner(); p = provider(tmp_path, r)
    (tmp_path / "kops-s-x").mkdir()
    p.destroy("kops-s-x")
    joined = [" ".join(c[0]) for c in r.calls]
    assert any("delete ns kops-s-x" in j for j in joined)
    assert any("delete secret kops-keys-kops-s-x" in j for j in joined)
    assert not (tmp_path / "kops-s-x").exists()


def test_list_owned_parses_managed_namespaces(tmp_path):
    out = json.dumps({"items": [
        {"metadata": {"name": "kops-s-a", "labels": {"kops.io/session": "s_a"},
                      "annotations": {"kops.io/owner": "alice", "kops.io/created": "1700000000"}}},
        {"metadata": {"name": "kops-s-b", "deletionTimestamp": "2026-10-03T00:00:00Z", "labels": {}}}]})
    refs = provider(tmp_path, FakeRunner({"get ns -l kops.io/managed=true": out})).list_owned()
    assert [(r.sandbox_id, r.owner, r.session_id) for r in refs] == [("kops-s-a", "alice", "s_a")]


def test_capacity_counts_requested_memory_and_skips_control_plane(tmp_path):
    nodes = {"items": [
        {"metadata": {"name": "cp"}, "spec": {"taints": [{"key": "node-role.kubernetes.io/control-plane"}]},
         "status": {"allocatable": {"memory": "8000000Ki"}}},
        {"metadata": {"name": "w1"}, "spec": {}, "status": {"allocatable": {"memory": "16384000Ki"}}}]}
    pods = {"items": [{"status": {"phase": "Running"}, "spec": {"nodeName": "w1", "containers": [
        {"resources": {"requests": {"memory": "4Gi"}}}]}}]}
    r = FakeRunner({"get nodes": json.dumps(nodes), "get pods -A": json.dumps(pods), "get ns -l": json.dumps({"items": []})})
    cap = provider(tmp_path, r).capacity()
    assert [n["name"] for n in cap.nodes] == ["w1"]
    assert cap.nodes[0]["memory_requested_mib"] == 4096
    assert cap.active_sessions == 0 and cap.max_sessions >= 2   # (16000*0.95-4096) // (4096+600)


def test_capacity_respects_configured_maximum(tmp_path):
    r = FakeRunner({"get nodes": json.dumps({"items": []}), "get pods -A": json.dumps({"items": []}),
                    "get ns -l": json.dumps({"items": []})})
    assert provider(tmp_path, r, max_sessions=7).capacity().max_sessions == 7


def test_provision_failure_cleans_up(tmp_path):
    class Boom(FakeRunner):
        def run(self, argv, **kw):
            if "apply" in argv and kw.get("input") and "VirtualMachine" in kw["input"]:
                return subprocess.CompletedProcess(argv, 1, "", "denied")
            return super().run(argv, **kw)
    r = Boom(); p = provider(tmp_path, r)
    try:
        p.provision(SandboxSpec(session_id="s_fail", owner="alice"), lambda m: None)
        raised = False
    except RuntimeError:
        raised = True
    assert raised
    assert any("delete ns kops-s-sfail" in " ".join(c[0]) for c in r.calls)


def test_list_owned_skips_exempt_selftest_namespaces_but_capacity_counts_them(tmp_path):
    out = json.dumps({"items": [
        {"metadata": {"name": "kops-s-a", "labels": {"kops.io/session": "s_a"}, "annotations": {"kops.io/owner": "alice"}}},
        {"metadata": {"name": "kops-s-st", "labels": {"kops.io/session": "st_1", "kops.io/exempt": "true"}, "annotations": {}}}]})
    p = provider(tmp_path, FakeRunner({"get ns -l kops.io/managed=true": out}))
    assert [r.sandbox_id for r in p.list_owned()] == ["kops-s-a"]
    assert [r.sandbox_id for r in p.list_owned(include_exempt=True)] == ["kops-s-a", "kops-s-st"]


def test_base_ssh_config_and_hosts_use_real_newlines(tmp_path):
    """Regression: the config was written with literal backslash-n sequences, so StrictHostKeyChecking never applied."""
    from kops.providers.kubevirt import KubeVirtSandbox
    r = FakeRunner(); p = provider(tmp_path, r)
    sb = KubeVirtSandbox(p, "s_x", "kops-s-x"); sb.dir.mkdir(parents=True)
    (sb.dir / "candidate.key").write_text("PRIVATE"); sb.key.write_text("PRIVATE")
    sb.ips = {"base": "10.0.0.1", "cp-1": "10.0.0.2", "w-1": "10.0.0.3"}
    p._prepare_base(sb, ["cp-1", "w-1"], "ssh-ed25519 AAAA")
    cmds = [c[0][-1] for c in r.calls if c[0][0] == "ssh"]
    base_cmd = cmds[0]
    assert "Host cp-1\n  HostName 10.0.0.2" in base_cmd            # a real newline, inside single quotes
    assert "\\n  HostName" not in base_cmd
    assert "StrictHostKeyChecking no" in base_cmd and "10.0.0.3 w-1" in base_cmd
