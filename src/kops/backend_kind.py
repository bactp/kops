"""Backend `kind`: one disposable cluster per trial, private kubeconfig, never the host's."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import threading
import time
from pathlib import Path

from . import config


class BackendError(Exception):
    """Infrastructure fault. A trial hitting this is INVALID, never FAIL."""


def _run(argv: list[str], *, env: dict | None = None, timeout: int = 120,
         input: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in argv], capture_output=True, text=True,
                          timeout=timeout, env=env, input=input)


def base_env(kubeconfig: Path) -> dict:
    """Scrubbed environment: nothing from the caller's shell, explicit KUBECONFIG only."""
    return {
        "PATH": f"{config.BIN_DIR}:/usr/bin:/bin",
        "HOME": str(config.RUN_DIR),
        "KUBECONFIG": str(kubeconfig),
        "LANG": "C.UTF-8",
    }


class KindCluster:
    def __init__(self, name: str):
        if not name.startswith(config.CLUSTER_PREFIX):
            raise BackendError(f"cluster name must start with {config.CLUSTER_PREFIX!r}")
        self.name = name
        config.RUN_DIR.mkdir(parents=True, exist_ok=True)
        self.admin_kubeconfig = config.RUN_DIR / f"{name}.admin.kubeconfig"
        self.agent_kubeconfig = config.RUN_DIR / f"{name}.agent.kubeconfig"
        self.created = False

    # -- lifecycle ---------------------------------------------------------
    def create(self) -> None:
        for img in config.PROFILE_IMAGES:
            if _run(["docker", "image", "inspect", img]).returncode != 0:
                r = _run(["docker", "pull", "-q", img], timeout=600)
                if r.returncode:
                    raise BackendError(f"docker pull {img} failed: {r.stderr.strip()}")
        r = _run([config.KIND, "create", "cluster", "--name", self.name,
                  "--image", config.KIND_NODE_IMAGE, "--kubeconfig", self.admin_kubeconfig,
                  "--wait", "180s"], timeout=600)
        self.created = True  # even a failed create may leave containers behind
        if r.returncode:
            raise BackendError(f"kind create failed: {r.stderr.strip()[-500:]}")
        self._assert_private_cluster()
        for img in config.PROFILE_IMAGES:
            # `kind load docker-image` breaks with Docker's containerd image store
            # (multi-platform manifests), so load a single-platform archive instead.
            r = _run([config.KIND, "load", "image-archive", self._image_archive(img),
                      "--name", self.name], timeout=300)
            if r.returncode:
                raise BackendError(f"kind load {img} failed: {r.stderr.strip()[-300:]}")
        self._provision_probe()
        # TODO(identity): the agent should be a distinct identity (client cert / RBAC)
        # so the API audit log can attribute mutations. Phase 1 copies admin credentials.
        shutil.copyfile(self.admin_kubeconfig, self.agent_kubeconfig)

    @staticmethod
    def _image_archive(img: str) -> Path:
        """Single-platform tar of a profile image, cached and shared by all clusters."""
        cache = config.RUN_DIR / "images"
        cache.mkdir(parents=True, exist_ok=True)
        tar = cache / (img.replace("/", "_").replace(":", "_") + ".tar")
        if not tar.exists():
            arch = "arm64" if platform.machine() in ("aarch64", "arm64") else "amd64"
            tmp = tar.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
            r = _run(["docker", "save", "--platform", f"linux/{arch}", "-o", tmp, img], timeout=300)
            if r.returncode:
                raise BackendError(f"docker save {img} failed: {r.stderr.strip()[-300:]}")
            os.replace(tmp, tar)
        return tar

    def delete(self) -> None:
        if self.created:
            _run([config.KIND, "delete", "cluster", "--name", self.name,
                  "--kubeconfig", self.admin_kubeconfig], timeout=120)
            self.created = False
        for p in (self.admin_kubeconfig, self.agent_kubeconfig):
            p.unlink(missing_ok=True)

    def container_exists(self) -> bool:
        r = _run(["docker", "ps", "-a", "--filter", f"name=^{self.name}-", "--format", "{{.Names}}"])
        return bool(r.stdout.strip())

    # -- safety -----------------------------------------------------------
    def _assert_private_cluster(self) -> None:
        """Refuse to continue unless the kubeconfig points at the kind cluster we just made."""
        r = self.kubectl("config", "view", "--minify", "-o", "json", check=True)
        cfg = json.loads(r.stdout)
        ctx = cfg["contexts"][0]["name"]
        server = cfg["clusters"][0]["cluster"]["server"]
        if ctx != f"kind-{self.name}" or not (
                server.startswith("https://127.0.0.1:") or server.startswith("https://localhost:")):
            raise BackendError(f"unexpected cluster context {ctx!r} / {server!r}; refusing to run")

    # -- verifier-side kubectl ---------------------------------------------
    def kubectl(self, *args: str, input: str | None = None, timeout: int = 60,
                check: bool = False) -> subprocess.CompletedProcess:
        r = _run([config.KUBECTL, *args], env=base_env(self.admin_kubeconfig),
                 timeout=timeout, input=input)
        if check and r.returncode:
            raise BackendError(f"kubectl {' '.join(args)} failed: {r.stderr.strip()[-400:]}")
        return r

    def _provision_probe(self) -> None:
        """Verifier-owned probe pod used by net.* checks. Not visible to the agent's task."""
        self.kubectl("create", "namespace", config.PROBE_NAMESPACE, check=True)
        self.kubectl("-n", config.PROBE_NAMESPACE, "run", config.PROBE_POD,
                     f"--image={config.PROBE_IMAGE}", "--image-pull-policy=IfNotPresent",
                     "--restart=Never", "--", "sleep", "86400", check=True)
        self.kubectl("-n", config.PROBE_NAMESPACE, "wait", "--for=condition=Ready",
                     f"pod/{config.PROBE_POD}", "--timeout=90s", check=True, timeout=120)

    def fingerprint(self) -> dict:
        ver = self.kubectl("version", "-o", "json").stdout
        try:
            server = json.loads(ver)["serverVersion"]["gitVersion"]
        except (KeyError, json.JSONDecodeError):
            server = None
        client = _run([config.KUBECTL, "version", "--client", "-o", "json"]).stdout
        return {"backend": "kind", "kubernetes_version": server,
                "node_image": config.KIND_NODE_IMAGE,
                "kind": _run([config.KIND, "version"]).stdout.strip(),
                "kubectl": json.loads(client)["clientVersion"]["gitVersion"],
                "profile_images": config.PROFILE_IMAGES}

    def snapshot_namespace(self, ns: str) -> str:
        r = self.kubectl("-n", ns, "get",
                         "deploy,rs,pods,svc,endpointslices,cm,secret,pvc,sa,role,rolebinding,"
                         "networkpolicy,ingress,hpa,job,cronjob,ds,sts",
                         "-o", "yaml")
        return r.stdout

    def wait_ready(self, ns: str, deadline_s: int = 120) -> None:
        t0 = time.monotonic()
        while time.monotonic() - t0 < deadline_s:
            r = self.kubectl("-n", ns, "get", "deploy", "-o", "json")
            if r.returncode == 0:
                items = json.loads(r.stdout)["items"]
                if items and all(i["status"].get("readyReplicas", 0) == i["spec"]["replicas"]
                                 for i in items):
                    return
            time.sleep(2)
        raise BackendError(f"deployments in {ns} not ready within {deadline_s}s")

    def run_setup(self, script: Path, env_extra: dict) -> None:
        env = base_env(self.admin_kubeconfig) | env_extra
        r = _run(["bash", "-eu", script], env=env, timeout=300)
        if r.returncode:
            raise BackendError(f"setup script failed ({r.returncode}): "
                               f"{(r.stderr or r.stdout).strip()[-500:]}")
