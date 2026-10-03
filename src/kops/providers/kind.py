"""KindProvider: one kind cluster per session. FOR DEVELOPER MACHINES AND CI ONLY.

There is no isolation between the candidate's shell and the host: `terminal_argv` is a local
`bash` with KUBECONFIG set, and the kubeconfig the candidate uses is a copy of the admin one.
Never use this provider for real users; the KubeVirt provider is the production one.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Callable

from .. import config
from ..backend_kind import KindCluster, _run
from .base import Capacity, SandboxRef, SandboxSpec, Target

PREFIX = f"{config.CLUSTER_PREFIX}s-"        # kops-s-<session id without "s_">


def cluster_name(session_id: str) -> str:
    return PREFIX + session_id.removeprefix("s_")


class KindSandbox:
    def __init__(self, cluster: KindCluster, session_id: str, workers: int):
        self.cluster, self.session_id, self.workers = cluster, session_id, workers
        self.id = cluster.name
        self.admin_kubeconfig = cluster.admin_kubeconfig

    def kubectl(self, *args: str, input: str | None = None, timeout: int = 60,
                check: bool = False) -> subprocess.CompletedProcess:
        return self.cluster.kubectl(*args, input=input, timeout=timeout, check=check)

    def run_setup(self, script: Path, env_extra: dict) -> None:
        self.cluster.run_setup(script, env_extra)

    def snapshot_namespace(self, ns: str) -> str:
        return self.cluster.snapshot_namespace(ns)

    def targets(self) -> list[Target]:
        return [Target("base", "base"), Target("cp-1", "node")] + \
               [Target(f"w-{i + 1}", "node") for i in range(self.workers)]

    def terminal_argv(self, target: str) -> list[str]:
        return ["env", f"KUBECONFIG={self.cluster.agent_kubeconfig}",
                f"PATH={config.BIN_DIR}:/usr/local/bin:/usr/bin:/bin", "bash", "--norc", "-i"]

    def fingerprint(self) -> dict:
        return self.cluster.fingerprint()


class KindProvider:
    name = "kind"

    def __init__(self, max_sessions: int = 2):
        self.max_sessions = max_sessions

    def _meta(self, name: str) -> Path:
        return config.RUN_DIR / f"{name}.meta.json"

    def provision(self, spec: SandboxSpec, progress: Callable[[str], None]) -> KindSandbox:
        name = cluster_name(spec.session_id)
        cl = KindCluster(name, workers=spec.workers)
        progress(f"creating kind cluster {name} (dev provider)")
        try:
            cl.create()
        except BaseException:
            cl.delete()
            raise
        self._meta(name).write_text(json.dumps({"session_id": spec.session_id, "owner": spec.owner,
                                                "workers": spec.workers, "created_at": time.time()}))
        progress("cluster ready")
        return KindSandbox(cl, spec.session_id, spec.workers)

    def attach(self, sandbox_id: str) -> KindSandbox:
        meta = json.loads(self._meta(sandbox_id).read_text())
        cl = KindCluster(sandbox_id, workers=meta.get("workers", 0))
        cl.created = True
        return KindSandbox(cl, meta["session_id"], meta.get("workers", 0))

    def recreate(self, sb: KindSandbox, progress: Callable[[str], None]) -> KindSandbox:
        progress("recreating kind cluster")
        sb.cluster.delete()
        sb.cluster.create()
        return sb

    def destroy(self, sandbox_id: str) -> None:
        if not sandbox_id.startswith(PREFIX):
            raise ValueError("refusing to destroy a cluster that is not a KOPS session cluster")
        cl = KindCluster(sandbox_id)
        cl.created = True
        cl.delete()
        self._meta(sandbox_id).unlink(missing_ok=True)

    def list_owned(self) -> list[SandboxRef]:
        r = _run([config.KIND, "get", "clusters"])
        out = []
        for name in r.stdout.split():
            if not name.startswith(PREFIX):
                continue
            try:
                meta = json.loads(self._meta(name).read_text())
            except (OSError, ValueError):
                meta = {"session_id": "s_" + name.removeprefix(PREFIX), "owner": "?", "created_at": 0}
            out.append(SandboxRef(name, meta["session_id"], meta["owner"], meta["created_at"]))
        return out

    def capacity(self) -> Capacity:
        return Capacity(self.max_sessions, len(self.list_owned()))
