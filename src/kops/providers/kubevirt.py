"""KubeVirtProvider: one namespace per session, VMs from a golden containerDisk image, a kubeadm cluster inside.

The provider is meant to run INSIDE the platform pod (namespace `kops-gw`): that is the only place the session
NetworkPolicies let it reach the VMs (ssh to `base`, the cluster API of the node). It needs the `kubectl` and
`ssh` binaries and the pod's ServiceAccount (see deploy/k8s).

Per session (namespace `kops-s-<id>`):
  base  - the candidate's entry host (ssh from the terminal gateway)
  cp-1  - kubeadm control plane (untainted when there are no workers)
  w-N   - optional workers
Everything boots from the same read-only image; writes live in a copy-on-write layer that is discarded when the VM
is deleted, so "reset by recreation" is simply delete + create.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .base import Capacity, SandboxRef, SandboxSpec, Target

PROBE_NS, PROBE_POD, PROBE_IMAGE = "kops-probe", "probe", "busybox:1.36.1"
GIB = 1024  # MiB


@dataclass
class KubeVirtSettings:
    image: str = "localhost/kops/node-golden:v3"
    platform_ns: str = "kops-gw"
    kubectl: str = "kubectl"
    ssh: str = "ssh"
    ssh_keygen: str = "ssh-keygen"
    kubeconfig: str | None = None          # None: in-cluster ServiceAccount
    work_dir: Path = Path("/var/run/kops")
    base: tuple[int, str] = (1, "1Gi")     # (vCPU, memory)
    cp: tuple[int, str] = (2, "3Gi")
    worker: tuple[int, str] = (2, "2Gi")
    vm_overhead_mib: int = 300
    max_sessions: int | None = None        # None: derived from free memory
    ssh_ready_timeout: int = 300
    cluster_ready_timeout: int = 420

    @staticmethod
    def from_env(env=os.environ) -> "KubeVirtSettings":
        s = KubeVirtSettings()
        s.image = env.get("KOPS_GOLDEN_IMAGE", s.image)
        s.platform_ns = env.get("KOPS_PLATFORM_NAMESPACE", s.platform_ns)
        s.kubeconfig = env.get("KOPS_KUBECONFIG") or None
        s.work_dir = Path(env.get("KOPS_WORK_DIR", str(s.work_dir)))
        if env.get("KOPS_MAX_SESSIONS"):
            s.max_sessions = int(env["KOPS_MAX_SESSIONS"])
        return s


def mem_mib(q: str) -> int:
    m = re.fullmatch(r"(\d+)(Gi|Mi|Ki)?", q)
    n, unit = int(m.group(1)), m.group(2) or ""
    return {"Gi": n * GIB, "Mi": n, "Ki": n // 1024, "": n // (1024 * 1024)}[unit]


class Runner:
    """Subprocess wrapper; tests replace it."""

    def run(self, argv: list[str], *, input: str | None = None, timeout: int = 60,
            env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([str(a) for a in argv], input=input, capture_output=True, text=True,
                              timeout=timeout, env=env)


def namespace_for(session_id: str) -> str:
    return "kops-s-" + re.sub(r"[^a-z0-9]", "", session_id.lower())[:12]


def label_safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)[:63] or "unknown"


# ----------------------------------------------------------------------------- manifests
def network_policies(platform_ns: str) -> list[dict]:
    """Default deny; free traffic inside the session; the platform may reach `base:22` and the node API only."""
    gw = [{"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": platform_ns}}}]
    def pol(name, spec): return {"apiVersion": "networking.k8s.io/v1", "kind": "NetworkPolicy",
                                 "metadata": {"name": name}, "spec": spec}
    return [
        pol("default-deny", {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]}),
        pol("intra-namespace", {"podSelector": {}, "policyTypes": ["Ingress", "Egress"],
                                "ingress": [{"from": [{"podSelector": {}}]}], "egress": [{"to": [{"podSelector": {}}]}]}),
        pol("platform-to-base-ssh", {"podSelector": {"matchLabels": {"role": "base"}}, "policyTypes": ["Ingress"],
                                     "ingress": [{"from": gw, "ports": [{"protocol": "TCP", "port": 22}]}]}),
        # DNS to the host cluster's CoreDNS only. Without it every name lookup in the guest waits for a timeout
        # (10 s for the VM's own hostname), which made kubeadm miss its deadline. Known leak: DNS tunnelling.
        pol("allow-dns", {"podSelector": {}, "policyTypes": ["Egress"], "egress": [{"to": [{
            "namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "kube-system"}},
            "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}}}],
            "ports": [{"protocol": "UDP", "port": 53}, {"protocol": "TCP", "port": 53}]}]}),
        # the platform builds the cluster over ssh and later reaches the API to grade; candidates never hold its key
        pol("platform-to-node", {"podSelector": {"matchLabels": {"role": "node"}}, "policyTypes": ["Ingress"],
                                 "ingress": [{"from": gw, "ports": [{"protocol": "TCP", "port": 6443},
                                                                    {"protocol": "TCP", "port": 22}]}]}),
    ]


def vm_manifest(name: str, role: str, cpu: int, memory: str, image: str, user_data: str, session_id: str) -> dict:
    return {
        "apiVersion": "kubevirt.io/v1", "kind": "VirtualMachine",
        "metadata": {"name": name, "labels": {"kops.io/session": label_safe(session_id)}},
        "spec": {"runStrategy": "Always", "template": {
            "metadata": {"labels": {"role": role, "kops.io/vm": name}},
            "spec": {"domain": {"cpu": {"cores": cpu}, "resources": {"requests": {"memory": memory}},
                                "devices": {"disks": [{"name": "root", "disk": {"bus": "virtio"}},
                                                      {"name": "ci", "disk": {"bus": "virtio"}}]}},
                     "volumes": [{"name": "root", "containerDisk": {"image": image, "imagePullPolicy": "IfNotPresent"}},
                                 {"name": "ci", "cloudInitNoCloud": {"userData": user_data}}]}}},
    }


def cloud_init(hostname: str, pubkeys: list[str]) -> str:
    keys = "\n".join(f"      - {json.dumps(k)}" for k in pubkeys)
    return ("#cloud-config\n"
            f"hostname: {hostname}\n"
            "manage_etc_hosts: localhost\n"
            "users:\n  - name: ubuntu\n    sudo: \"ALL=(ALL) NOPASSWD:ALL\"\n    shell: /bin/bash\n"
            f"    ssh_authorized_keys:\n{keys}\n")


# ----------------------------------------------------------------------------- sandbox
class KubeVirtSandbox:
    def __init__(self, provider: "KubeVirtProvider", session_id: str, ns: str):
        self.p, self.session_id, self.id = provider, session_id, ns
        self.dir = provider.cfg.work_dir / ns
        self.admin_kubeconfig = self.dir / "verifier.kubeconfig"
        self.key = self.dir / "platform.key"
        self.ips: dict[str, str] = {}

    # verifier-side API
    def kubectl(self, *args: str, input: str | None = None, timeout: int = 60, check: bool = False):
        r = self.p.run([self.p.cfg.kubectl, "--kubeconfig", str(self.admin_kubeconfig), *args],
                       input=input, timeout=timeout)
        if check and r.returncode:
            raise RuntimeError(f"kubectl {' '.join(args)} failed: {r.stderr.strip()[-400:]}")
        return r

    def run_setup(self, script: Path, env_extra: dict) -> None:
        env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": str(self.dir),
               "KUBECONFIG": str(self.admin_kubeconfig), "LANG": "C.UTF-8", **env_extra}
        r = self.p.runner.run(["bash", "-eu", str(script)], timeout=300, env=env)
        if r.returncode:
            raise RuntimeError(f"setup script failed ({r.returncode}): {(r.stderr or r.stdout).strip()[-500:]}")

    def snapshot_namespace(self, ns: str) -> str:
        return self.kubectl("-n", ns, "get", "deploy,rs,pods,svc,endpointslices,cm,pvc,sa,role,rolebinding,"
                            "networkpolicy,ingress,hpa,job,cronjob,ds,sts", "-o", "yaml").stdout

    def targets(self) -> list[Target]:
        return [Target(n, "base" if n == "base" else "node") for n in self.ips]

    def terminal_argv(self, target: str) -> list[str]:
        if target not in self.ips:
            raise KeyError(target)
        base = [self.p.cfg.ssh, "-i", str(self.key), "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR", "-tt", f"ubuntu@{self.ips['base']}"]
        # the candidate reaches the cluster hosts from `base`, as in the exam
        return base if target == "base" else base + [f"ssh -tt {target}"]

    def fingerprint(self) -> dict:
        return {"backend": "kubevirt", "image": self.p.cfg.image, "namespace": self.id, "vms": dict(self.ips)}

    # helpers
    def ssh_run(self, host: str, command: str, *, input: str | None = None, timeout: int = 120):
        return self.p.run([self.p.cfg.ssh, "-i", str(self.key), "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
                           "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                           "-o", "LogLevel=ERROR", f"ubuntu@{self.ips[host]}", command], input=input, timeout=timeout)


# ----------------------------------------------------------------------------- provider
class KubeVirtProvider:
    name = "kubevirt"

    def __init__(self, cfg: KubeVirtSettings | None = None, runner: Runner | None = None):
        self.cfg = cfg or KubeVirtSettings.from_env()
        self.runner = runner or Runner()
        self.cfg.work_dir.mkdir(parents=True, exist_ok=True)

    # kubectl against the HOST cluster (the one running KubeVirt)
    def run(self, argv: list[str], **kw) -> subprocess.CompletedProcess:
        if argv and argv[0] == self.cfg.kubectl and self.cfg.kubeconfig:
            argv = [argv[0], "--kubeconfig", self.cfg.kubeconfig, *argv[1:]]
        return self.runner.run(argv, **kw)

    def kube(self, *args: str, input: str | None = None, timeout: int = 60, check: bool = True):
        r = self.run([self.cfg.kubectl, *args], input=input, timeout=timeout)
        if check and r.returncode:
            raise RuntimeError(f"kubectl {' '.join(args[:4])}... failed: {r.stderr.strip()[-400:]}")
        return r

    def apply(self, doc: dict | list, ns: str | None = None) -> None:
        docs = doc if isinstance(doc, list) else [doc]
        body = "\n---\n".join(json.dumps(d) for d in docs)
        self.kube(*(["-n", ns] if ns else []), "apply", "-f", "-", input=body)

    # ---- provisioning
    def provision(self, spec: SandboxSpec, progress: Callable[[str], None]):
        ns = namespace_for(spec.session_id)
        sb = KubeVirtSandbox(self, spec.session_id, ns)
        sb.dir.mkdir(parents=True, exist_ok=True)
        try:
            progress(f"creating namespace {ns}")
            self.apply({"apiVersion": "v1", "kind": "Namespace", "metadata": {
                "name": ns, "labels": {"kops.io/managed": "true", "kops.io/session": label_safe(spec.session_id),
                                       "kops.io/owner": label_safe(spec.owner), **spec.labels},
                "annotations": {"kops.io/owner": spec.owner, "kops.io/created": str(int(time.time())),
                                "kops.io/ttl": str(spec.ttl_seconds), "kops.io/workers": str(spec.workers)}}})
            self.apply(network_policies(self.cfg.platform_ns), ns)
            self._keys(sb)
            self._boot_cluster(sb, spec, progress)
            self._save_secret(sb)
            return sb
        except Exception:
            if os.environ.get("KOPS_KEEP_FAILED") == "1":   # debugging aid: leave the sandbox for inspection
                progress(f"provisioning failed; keeping {ns} (KOPS_KEEP_FAILED=1)")
            else:
                self.destroy(ns)
            raise

    def _keys(self, sb: KubeVirtSandbox) -> None:
        for name in ("platform.key", "candidate.key"):
            f = sb.dir / name
            if not f.exists():
                self.runner.run([self.cfg.ssh_keygen, "-q", "-t", "ed25519", "-N", "", "-f", str(f)], timeout=20)
        os.chmod(sb.key, 0o600)

    def _pub(self, sb, name: str) -> str:
        return (sb.dir / f"{name}.key.pub").read_text().strip()

    def _create_vm(self, sb, name, role, size, spec_pub):
        cpu, mem = size
        self.apply(vm_manifest(name, role, cpu, mem, self.cfg.image, cloud_init(name, spec_pub), sb.session_id), sb.id)

    def _vm_ip(self, sb, name) -> str:
        r = self.kube("-n", sb.id, "get", "vmi", name, "-o", "jsonpath={.status.interfaces[0].ipAddress}", check=False)
        return r.stdout.strip()

    def _wait_ssh(self, sb, name, progress) -> None:
        t0 = time.time()
        while time.time() - t0 < self.cfg.ssh_ready_timeout:
            ip = self._vm_ip(sb, name)
            if ip:
                sb.ips[name] = ip
                if sb.ssh_run(name, "true", timeout=15).returncode == 0:
                    progress(f"{name} reachable ({ip}) after {int(time.time() - t0)}s")
                    return
            time.sleep(2)
        raise TimeoutError(f"{name} did not become reachable in {self.cfg.ssh_ready_timeout}s")

    def _boot_cluster(self, sb: KubeVirtSandbox, spec: SandboxSpec, progress) -> None:
        cand_pub = self._pub(sb, "candidate")
        plat_pub = self._pub(sb, "platform")
        nodes = ["cp-1"] + [f"w-{i}" for i in range(1, spec.workers + 1)]
        progress("creating VMs: base " + " ".join(nodes))
        self._create_vm(sb, "base", "base", self.cfg.base, [plat_pub])
        self._create_vm(sb, "cp-1", "node", self.cfg.cp, [plat_pub, cand_pub])
        for w in nodes[1:]:
            self._create_vm(sb, w, "node", self.cfg.worker, [plat_pub, cand_pub])
        for name in ["base"] + nodes:
            self._wait_ssh(sb, name, progress)
        cp = sb.ips["cp-1"]
        progress("kubeadm init")
        init = (f"sudo kubeadm init --kubernetes-version \"$(kubeadm version -o short)\" --node-name cp-1 "
                f"--apiserver-advertise-address {cp} --apiserver-cert-extra-sans {cp} "
                "--pod-network-cidr 192.168.0.0/16 --ignore-preflight-errors=NumCPU >/tmp/init.log 2>&1 "
                "&& mkdir -p ~/.kube && sudo cp /etc/kubernetes/admin.conf ~/.kube/config && sudo chown ubuntu: ~/.kube/config "
                "&& kubectl apply -f /opt/cni/calico.yaml >/dev/null && kubectl apply -f /opt/cni/local-path.yaml >/dev/null")
        r = sb.ssh_run("cp-1", init, timeout=300)
        if r.returncode:
            tail = sb.ssh_run("cp-1", "tail -5 /tmp/init.log", timeout=20).stdout
            raise RuntimeError(f"kubeadm init failed: {tail.strip()[-400:]}")
        if spec.workers == 0:
            sb.ssh_run("cp-1", "kubectl taint nodes --all node-role.kubernetes.io/control-plane- >/dev/null 2>&1 || true")
        else:
            join = sb.ssh_run("cp-1", "sudo kubeadm token create --ttl 30m --print-join-command", timeout=30).stdout.strip()
            for w in nodes[1:]:
                progress(f"joining {w}")
                rj = sb.ssh_run(w, f"sudo {join} --node-name {w} >/tmp/join.log 2>&1", timeout=180)
                if rj.returncode:
                    raise RuntimeError(f"join of {w} failed")
        self._wait_ready(sb, len(nodes), progress)
        # verifier identity: minted on the node, kept outside the VMs
        kc = sb.ssh_run("cp-1", "sudo kubeadm kubeconfig user --client-name kops-verifier --org system:masters", timeout=30)
        if kc.returncode or "server:" not in kc.stdout:
            raise RuntimeError("could not mint the verifier kubeconfig")
        sb.admin_kubeconfig.write_text(kc.stdout)
        os.chmod(sb.admin_kubeconfig, 0o600)
        self._probe(sb, spec.workers > 0)
        self._prepare_base(sb, nodes, cand_pub)

    def _wait_ready(self, sb, expected: int, progress) -> None:
        t0 = time.time()
        while time.time() - t0 < self.cfg.cluster_ready_timeout:
            r = sb.ssh_run("cp-1", "kubectl get nodes --no-headers 2>/dev/null | grep -c ' Ready'", timeout=20)
            if r.stdout.strip() == str(expected):
                r2 = sb.ssh_run("cp-1", "kubectl -n local-path-storage get deploy local-path-provisioner "
                                "-o jsonpath='{.status.readyReplicas}' 2>/dev/null", timeout=20)
                if r2.stdout.strip().strip("'") == "1":
                    progress(f"cluster ready: {expected} node(s) after {int(time.time() - t0)}s")
                    return
            time.sleep(3)
        raise TimeoutError("the cluster did not become Ready")

    def _probe(self, sb, has_workers: bool) -> None:
        sb.kubectl("create", "namespace", PROBE_NS, check=True)
        overrides = []
        if has_workers:  # keep the verifier's client off the nodes that scenarios drain or cordon
            overrides = ["--overrides=" + json.dumps({"spec": {
                "nodeSelector": {"node-role.kubernetes.io/control-plane": ""},
                "tolerations": [{"key": "node-role.kubernetes.io/control-plane", "operator": "Exists", "effect": "NoSchedule"}]}})]
        sb.kubectl("-n", PROBE_NS, "run", PROBE_POD, f"--image={PROBE_IMAGE}", "--image-pull-policy=IfNotPresent",
                   "--restart=Never", *overrides, "--", "sleep", "86400", check=True)
        sb.kubectl("-n", PROBE_NS, "wait", "--for=condition=Ready", f"pod/{PROBE_POD}", "--timeout=120s",
                   check=True, timeout=150)

    def _prepare_base(self, sb, nodes, cand_pub) -> None:
        hosts = "\n".join(f"{sb.ips[n]} {n}" for n in nodes)
        cfg = "\n".join(f"Host {n}\n  HostName {sb.ips[n]}\n  User ubuntu\n  StrictHostKeyChecking no\n  UserKnownHostsFile /dev/null\n  LogLevel ERROR" for n in nodes)
        script = (f"set -e; mkdir -p ~/.ssh; chmod 700 ~/.ssh; cat > ~/.ssh/id_ed25519; chmod 600 ~/.ssh/id_ed25519; "
                  f"printf '%s\\n' {shlex.quote(cfg)} > ~/.ssh/config; chmod 600 ~/.ssh/config; "
                  f"printf '%s\\n' {shlex.quote(hosts)} | sudo tee -a /etc/hosts >/dev/null")
        r = sb.ssh_run("base", script, input=(sb.dir / "candidate.key").read_text(), timeout=30)
        if r.returncode:
            raise RuntimeError(f"preparing base failed: {r.stderr.strip()[-300:]}")
        for n in nodes:  # name resolution between cluster hosts
            sb.ssh_run(n, f"printf '%s\\n' {shlex.quote(hosts)} | sudo tee -a /etc/hosts >/dev/null", timeout=30)

    # ---- persistence across platform restarts
    def _secret_name(self, ns: str) -> str:
        return f"kops-keys-{ns}"

    def _save_secret(self, sb) -> None:
        files = {"platform.key": sb.key, "candidate.key": sb.dir / "candidate.key", "verifier.kubeconfig": sb.admin_kubeconfig}
        args = ["-n", self.cfg.platform_ns, "create", "secret", "generic", self._secret_name(sb.id), "--dry-run=client",
                "-o", "yaml"] + [f"--from-file={k}={v}" for k, v in files.items()]
        manifest = self.kube(*args).stdout
        self.kube("apply", "-f", "-", input=manifest)
        self.kube("-n", self.cfg.platform_ns, "label", "secret", self._secret_name(sb.id),
                  f"kops.io/session={label_safe(sb.session_id)}", "--overwrite")

    def attach(self, sandbox_id: str):
        ns = sandbox_id
        meta = json.loads(self.kube("get", "ns", ns, "-o", "json").stdout)["metadata"]
        sb = KubeVirtSandbox(self, meta["labels"]["kops.io/session"], ns)
        sb.dir.mkdir(parents=True, exist_ok=True)
        sec = json.loads(self.kube("-n", self.cfg.platform_ns, "get", "secret", self._secret_name(ns), "-o", "json").stdout)
        import base64
        for k, f in {"platform.key": sb.key, "candidate.key": sb.dir / "candidate.key",
                     "verifier.kubeconfig": sb.admin_kubeconfig}.items():
            f.write_bytes(base64.b64decode(sec["data"][k])); os.chmod(f, 0o600)
        vmis = json.loads(self.kube("-n", ns, "get", "vmi", "-o", "json").stdout)["items"]
        for v in vmis:
            ip = (v["status"].get("interfaces") or [{}])[0].get("ipAddress")
            if ip:
                sb.ips[v["metadata"]["name"]] = ip
        return sb

    def recreate(self, sb: KubeVirtSandbox, progress):
        progress("deleting VMs")
        workers = len([n for n in sb.ips if n.startswith("w-")])
        self.kube("-n", sb.id, "delete", "vm", "--all", "--wait=true", timeout=180)
        sb.ips.clear()
        spec = SandboxSpec(session_id=sb.session_id, owner="", workers=workers)
        self._boot_cluster(sb, spec, progress)
        self._save_secret(sb)
        return sb

    def destroy(self, sandbox_id: str) -> None:
        self.kube("delete", "ns", sandbox_id, "--ignore-not-found", "--wait=false", check=False)
        self.kube("-n", self.cfg.platform_ns, "delete", "secret", self._secret_name(sandbox_id), "--ignore-not-found", check=False)
        shutil.rmtree(self.cfg.work_dir / sandbox_id, ignore_errors=True)

    def list_owned(self, include_exempt: bool = False) -> list[SandboxRef]:
        """Sandboxes the sweeper may destroy. Namespaces labelled `kops.io/exempt=true` (selftest runs) are skipped
        unless `include_exempt` is set, which capacity accounting uses."""
        r = self.kube("get", "ns", "-l", "kops.io/managed=true", "-o", "json", check=False)
        if r.returncode:
            return []
        out = []
        for it in json.loads(r.stdout)["items"]:
            md = it["metadata"]
            if md.get("deletionTimestamp"):
                continue
            if md.get("labels", {}).get("kops.io/exempt") == "true" and not include_exempt:
                continue
            ann = md.get("annotations", {})
            out.append(SandboxRef(md["name"], md["labels"].get("kops.io/session", ""), ann.get("kops.io/owner", ""),
                                  float(ann.get("kops.io/created", "0"))))
        return out

    def capacity(self) -> Capacity:
        nodes = json.loads(self.kube("get", "nodes", "-o", "json").stdout)["items"]
        pods = json.loads(self.kube("get", "pods", "-A", "-o", "json", timeout=90).stdout)["items"]
        req: dict[str, int] = {}
        for p in pods:
            if p["status"].get("phase") in ("Succeeded", "Failed") or not p["spec"].get("nodeName"):
                continue
            m = sum(mem_mib(c.get("resources", {}).get("requests", {}).get("memory", "0")) for c in p["spec"]["containers"]
                    if re.fullmatch(r"\d+(Gi|Mi|Ki)?", c.get("resources", {}).get("requests", {}).get("memory", "0") or "0"))
            req[p["spec"]["nodeName"]] = req.get(p["spec"]["nodeName"], 0) + m
        info, free = [], 0
        for n in nodes:
            if n["spec"].get("taints") and any(t["key"].endswith("control-plane") for t in n["spec"]["taints"]):
                continue
            alloc = int(re.sub(r"\D", "", n["status"]["allocatable"]["memory"])) // 1024  # Ki -> MiB
            used = req.get(n["metadata"]["name"], 0)
            info.append({"name": n["metadata"]["name"], "memory_allocatable_mib": alloc, "memory_requested_mib": used})
            free += max(0, int(alloc * 0.95) - used)
        active = len(self.list_owned(include_exempt=True))
        per = sum(mem_mib(m) + self.cfg.vm_overhead_mib for _, m in (self.cfg.base, self.cfg.cp))
        mx = self.cfg.max_sessions if self.cfg.max_sessions is not None else active + free // per
        return Capacity(max_sessions=mx, active_sessions=active, nodes=info)
