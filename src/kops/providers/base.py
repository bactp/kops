"""The contract between the platform and a sandbox provider.

A `Sandbox` is a cluster plus the hosts a candidate can open a shell on. It exposes the same
`kubectl()` / `run_setup()` / `snapshot_namespace()` surface that `KindCluster` has, so the existing
`Verifier` works against it unchanged.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol


@dataclass
class SandboxSpec:
    session_id: str
    owner: str
    workers: int = 0                  # extra worker nodes besides the control plane
    ttl_seconds: int = 7200
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class Target:
    name: str                         # "base", "cp-1", "w-1"
    role: str                         # "base" | "node"


@dataclass
class SandboxRef:
    sandbox_id: str
    session_id: str
    owner: str
    created_at: float                 # unix seconds


@dataclass
class Capacity:
    max_sessions: int
    active_sessions: int
    nodes: list[dict] = field(default_factory=list)   # {"name","memory_allocatable_mib","memory_requested_mib"}


class Sandbox(Protocol):
    id: str
    session_id: str
    admin_kubeconfig: Path            # verifier identity, never given to the candidate

    def kubectl(self, *args: str, input: str | None = None, timeout: int = 60,
                check: bool = False) -> subprocess.CompletedProcess:
        """Run kubectl against the sandbox cluster as the verifier."""

    def run_setup(self, script: Path, env_extra: dict) -> None:
        """Run a scenario setup script with the verifier's kubeconfig; raise on failure."""

    def snapshot_namespace(self, ns: str) -> str: ...

    def targets(self) -> list[Target]: ...

    def terminal_argv(self, target: str) -> list[str]:
        """argv that opens an interactive shell on `target`; the platform runs it inside a pty."""

    def fingerprint(self) -> dict: ...


class SandboxProvider(Protocol):
    name: str

    def provision(self, spec: SandboxSpec, progress: Callable[[str], None]) -> Sandbox:
        """Create the sandbox and block until it is ready. `progress` receives log lines."""

    def attach(self, sandbox_id: str) -> Sandbox:
        """Re-attach to an existing sandbox (after a platform restart)."""

    def recreate(self, sb: Sandbox, progress: Callable[[str], None]) -> Sandbox:
        """Reset by recreation: destroy the VMs and bring up a fresh cluster in the same sandbox."""

    def adopt(self, sandbox_id: str, session_id: str, owner: str, ttl_seconds: int) -> Sandbox:
        """Re-label an existing sandbox for another session (used to hand out warm-pool sandboxes)."""

    def destroy(self, sandbox_id: str) -> None: ...

    def list_owned(self) -> list[SandboxRef]:
        """Every sandbox this provider created, for the orphan sweeper."""

    def capacity(self) -> Capacity: ...
