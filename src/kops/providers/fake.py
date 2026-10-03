"""In-memory provider for tests: no cluster, no docker, no network.

`FakeSandbox.kubectl` serves a tiny object store (get/create/apply/replace/delete of JSON
objects) so the real `Verifier` and `Reset` can run against it. Tests mutate `sandbox.objects`
to play the candidate.
"""
from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable

from .base import Capacity, SandboxRef, SandboxSpec, Target

_ALIASES = {"cm": "configmap", "ns": "namespace", "sa": "serviceaccount", "deploy": "deployment",
            "svc": "service", "ds": "daemonset", "sts": "statefulset", "pvc": "persistentvolumeclaim",
            "pv": "persistentvolume", "hpa": "horizontalpodautoscaler", "pdb": "poddisruptionbudget",
            "sc": "storageclass", "netpol": "networkpolicy", "ing": "ingress"}
_CLUSTER_SCOPED = {"namespace", "storageclass", "clusterrole", "clusterrolebinding", "priorityclass",
                   "persistentvolume", "node"}


def norm_kind(kind: str) -> str:
    k = kind.lower().split("/")[0].split(".")[0]
    if k in _ALIASES:
        return _ALIASES[k]
    if k.endswith("ies"):
        return k[:-3] + "y"
    if k.endswith("sses"):
        return k[:-2]
    return k[:-1] if k.endswith("s") else k


def _done(rc: int = 0, out: str = "", err: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(["kubectl"], rc, out, err)


class FakeSandbox:
    def __init__(self, sandbox_id: str, session_id: str, workers: int = 0):
        self.id, self.session_id = sandbox_id, session_id
        self.admin_kubeconfig = Path("/nonexistent/fake-admin.kubeconfig")
        self.workers = workers
        self.objects: dict[tuple[str, str, str], dict] = {}   # (kind, namespace, name) -> object
        self.calls: list[tuple] = []
        self.setup_calls: list[tuple[Path, dict]] = []
        self.setup_hook: Callable[["FakeSandbox", Path, dict], None] | None = None
        self.hooks: list[Callable[[tuple, str | None], subprocess.CompletedProcess | None]] = []

    # -- Sandbox protocol -------------------------------------------------------------------
    def kubectl(self, *args: str, input: str | None = None, timeout: int = 60,
                check: bool = False) -> subprocess.CompletedProcess:
        self.calls.append(args)
        r = None
        for h in self.hooks:
            r = h(args, input)
            if r is not None:
                break
        if r is None:
            r = self._serve(list(args), input)
        if check and r.returncode:
            raise RuntimeError(f"fake kubectl failed: {r.stderr}")
        return r

    def run_setup(self, script: Path, env_extra: dict) -> None:
        self.setup_calls.append((script, dict(env_extra)))
        if self.setup_hook:
            self.setup_hook(self, script, env_extra)

    def snapshot_namespace(self, ns: str) -> str:
        return json.dumps([v for k, v in sorted(self.objects.items()) if k[1] == ns], sort_keys=True)

    def targets(self) -> list[Target]:
        return [Target("base", "base"), Target("cp-1", "node")] + \
               [Target(f"w-{i + 1}", "node") for i in range(self.workers)]

    def terminal_argv(self, target: str) -> list[str]:
        return ["bash", "--norc"]

    def fingerprint(self) -> dict:
        return {"backend": "fake"}

    # -- helpers for tests ------------------------------------------------------------------
    def put(self, kind: str, name: str, namespace: str = "", **body) -> dict:
        kind = norm_kind(kind)
        obj = {"kind": kind, "metadata": {"name": name, **({"namespace": namespace} if namespace else {})}}
        obj.update(body)
        self.objects[(kind, namespace, name)] = obj
        return obj

    def has(self, kind: str, name: str, namespace: str = "") -> bool:
        return (norm_kind(kind), namespace, name) in self.objects

    # -- tiny kubectl -----------------------------------------------------------------------
    def _serve(self, a: list[str], stdin: str | None) -> subprocess.CompletedProcess:
        ns, all_ns, sel, pos, flags = "", False, None, [], set()
        i = 0
        while i < len(a):
            x = a[i]
            if x == "-n":
                ns, i = a[i + 1], i + 1
            elif x == "-A":
                all_ns = True
            elif x == "-l":
                sel, i = a[i + 1], i + 1
            elif x in ("-o", "-f"):
                i += 1
            elif x.startswith("-"):
                flags.add(x)
            else:
                pos.append(x)
            i += 1
        if not pos:
            return _done(1, err="fake kubectl: no verb")
        verb, rest = pos[0], pos[1:]
        if verb == "get" and rest:
            return self._get(norm_kind(rest[0]), rest[1] if len(rest) > 1 else None, ns, all_ns, sel)
        if verb == "delete" and len(rest) >= 2:
            return self._delete(norm_kind(rest[0]), rest[1], ns, "--ignore-not-found" in flags)
        if verb in ("create", "apply", "replace") and stdin:
            return self._write(verb, json.loads(stdin))
        return _done(1, err=f"fake kubectl: unsupported {' '.join(a)}")

    def _get(self, kind, name, ns, all_ns, sel) -> subprocess.CompletedProcess:
        if name:
            key = (kind, "" if kind in _CLUSTER_SCOPED else ns, name)
            if key not in self.objects:
                return _done(1, err=f'Error from server (NotFound): {kind} "{name}" not found')
            return _done(out=json.dumps(self.objects[key]))
        want = dict(p.split("=", 1) for p in sel.split(",")) if sel else {}
        items = []
        for (k, n, _), o in sorted(self.objects.items()):
            if k != kind or (n != ns and not all_ns and kind not in _CLUSTER_SCOPED and ns):
                continue
            labels = o.get("metadata", {}).get("labels", {})
            if all(labels.get(lk) == lv for lk, lv in want.items()):
                items.append(o)
        return _done(out=json.dumps({"items": items}))

    def _delete(self, kind, name, ns, ignore_missing) -> subprocess.CompletedProcess:
        key = (kind, "" if kind in _CLUSTER_SCOPED else ns, name)
        if key not in self.objects:
            return _done(0 if ignore_missing else 1, err=f'Error from server (NotFound): {kind} "{name}" not found')
        del self.objects[key]
        if kind == "namespace":
            for k in [k for k in self.objects if k[1] == name]:
                del self.objects[k]
        return _done(out="deleted")

    def _write(self, verb, obj) -> subprocess.CompletedProcess:
        kind, md = norm_kind(obj.get("kind", "")), obj.get("metadata", {})
        key = (kind, md.get("namespace", ""), md.get("name", ""))
        if verb == "create" and key in self.objects:
            return _done(1, err="AlreadyExists")
        if verb == "replace" and key not in self.objects:
            return _done(1, err="NotFound")
        self.objects[key] = obj
        return _done(out=verb)


class FakeProvider:
    name = "fake"

    def __init__(self, max_sessions: int = 4, provision_delay: float = 0.0):
        self.max_sessions = max_sessions
        self.provision_delay = provision_delay
        self.sandboxes: dict[str, FakeSandbox] = {}
        self.refs: dict[str, SandboxRef] = {}
        self.fail_provision: str | None = None    # message: provision() raises
        self.fail_recreate: str | None = None
        self.setup_hook: Callable[[FakeSandbox, Path, dict], None] | None = None
        self.recreated: list[str] = []
        self.destroyed: list[str] = []
        self._n = 0
        self._lock = threading.Lock()

    def provision(self, spec: SandboxSpec, progress: Callable[[str], None]) -> FakeSandbox:
        progress("fake: creating sandbox")
        if self.provision_delay:
            time.sleep(self.provision_delay)
        if self.fail_provision:
            raise RuntimeError(self.fail_provision)
        with self._lock:
            self._n += 1
            sid = f"fake-{self._n}"
            sb = FakeSandbox(sid, spec.session_id, spec.workers)
            sb.setup_hook = self.setup_hook
            self.sandboxes[sid] = sb
            self.refs[sid] = SandboxRef(sid, spec.session_id, spec.owner, time.time())
        progress("fake: sandbox ready")
        return sb

    def attach(self, sandbox_id: str) -> FakeSandbox:
        if sandbox_id not in self.sandboxes:
            raise KeyError(f"unknown sandbox {sandbox_id}")
        return self.sandboxes[sandbox_id]

    def recreate(self, sb: FakeSandbox, progress: Callable[[str], None]) -> FakeSandbox:
        progress("fake: recreating sandbox")
        if self.fail_recreate:
            raise RuntimeError(self.fail_recreate)
        sb.objects.clear()
        self.recreated.append(sb.id)
        return sb

    def destroy(self, sandbox_id: str) -> None:
        self.sandboxes.pop(sandbox_id, None)
        self.refs.pop(sandbox_id, None)
        self.destroyed.append(sandbox_id)

    def list_owned(self) -> list[SandboxRef]:
        return list(self.refs.values())

    def capacity(self) -> Capacity:
        return Capacity(self.max_sessions, len(self.sandboxes),
                        [{"name": "fake-node-1", "memory_allocatable_mib": 16000,
                          "memory_requested_mib": 1000 * len(self.sandboxes)}])

    # test helper
    def add_orphan(self, session_id: str = "s_orphan", owner: str = "ghost") -> str:
        sid = f"fake-orphan-{len(self.refs) + 1}"
        self.sandboxes[sid] = FakeSandbox(sid, session_id)
        self.refs[sid] = SandboxRef(sid, session_id, owner, time.time())
        return sid
