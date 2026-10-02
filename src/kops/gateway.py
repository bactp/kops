"""Tool Gateway: the only path from an agent to the cluster.

Phase 1 exposes a single tool, `kubectl`. Enforces budgets, timeouts, output
truncation, and records every attempt (including rejected ones) in the trace.
"""
from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .backend_kind import base_env

MUTATING_VERBS = {"apply", "create", "patch", "set", "scale", "delete", "replace", "label",
                  "annotate", "edit", "expose", "run", "taint", "cordon", "uncordon", "drain",
                  "autoscale"}
MUTATING_ROLLOUT = {"undo", "restart", "pause", "resume"}
READ_VERBS = {"get", "describe", "logs", "top", "explain", "api-resources", "api-versions", "diff",
              "events", "auth", "cluster-info", "config", "version", "wait", "exec", "port-forward",
              "cp", "attach", "rollout", "certificate", "debug", "plugin", "proxy", "kustomize"}
KNOWN_VERBS = MUTATING_VERBS | READ_VERBS
FORBIDDEN_FLAGS = ("--kubeconfig", "--server", "-s", "--token", "--as", "--as-group",
                   "--certificate-authority", "--client-certificate", "--client-key",
                   "--insecure-skip-tls-verify", "--username", "--password")
SHELL_TOKENS = {"|", "||", "&&", ";", ">", ">>", "<", "&", "2>&1"}
# stderr fragments that mean "the command itself was malformed" (heuristic; versioned list).
INVALID_STDERR_PATTERNS = (
    "unknown command", "unknown flag", "unknown shorthand flag", "invalid argument",
    "error: required flag", "flag needs an argument", "unexpected argument",
    "doesn't have a resource type", "you must specify", "error: unknown",
    "accepts at most", "accepts between", "requires at least", "expected 'kubectl",
    "error: must specify", "invalid resource",
)
INVALID_PATTERNS_VERSION = "1"


class BudgetExhausted(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason  # "steps" | "wall_clock"


@dataclass
class Observation:
    kind: str             # ok | exec_error | timeout | policy_rejected | parse_error
    exit_code: int | None
    stdout: str
    stderr: str
    truncated: bool = False
    duration_ms: int = 0

    def render(self) -> str:
        """Identical presentation for every agent."""
        if self.kind == "policy_rejected" or self.kind == "parse_error":
            return self.stderr
        parts = [f"[exit code: {self.exit_code}]" if self.kind != "timeout" else "[TIMEOUT]"]
        if self.stdout:
            parts.append(self.stdout.rstrip("\n"))
        if self.stderr:
            parts.append("[stderr]\n" + self.stderr.rstrip("\n"))
        if self.truncated:
            parts.append("[output truncated]")
        return "\n".join(parts)


@dataclass
class Trace:
    events: list[dict] = field(default_factory=list)

    def add(self, **ev) -> dict:
        ev = {"seq": len(self.events) + 1, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **ev}
        self.events.append(ev)
        return ev

    def write(self, path: Path) -> None:
        path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in self.events))


def classify_command(argv: list[str]) -> tuple[bool, bool]:
    """(mutating, dry_run) from kubectl argv without the leading 'kubectl'."""
    dry = any(a.startswith("--dry-run") and a not in ("--dry-run=none", "--dry-run=false")
              for a in argv)
    # Flag values (e.g. the namespace after -n) must not be mistaken for the verb:
    # take the first token that is a known kubectl verb.
    words = [a for a in argv if not a.startswith("-")]
    idx = next((i for i, w in enumerate(words) if w in KNOWN_VERBS), None)
    if idx is None:
        return False, dry
    verb = words[idx]
    mutating = verb in MUTATING_VERBS or (verb == "rollout" and len(words) > idx + 1
                                          and words[idx + 1] in MUTATING_ROLLOUT)
    return mutating and not dry, dry


class Gateway:
    def __init__(self, kubeconfig: Path, trace: Trace, *, max_steps: int, max_wall_s: float,
                 per_action_timeout_s: int, max_output_bytes: int = 8192, run_cmd=None):
        self.kubeconfig, self.trace = kubeconfig, trace
        self.max_steps, self.per_action_timeout_s = max_steps, per_action_timeout_s
        self.max_output_bytes = max_output_bytes
        self.deadline = time.monotonic() + max_wall_s
        self.steps = 0
        self._run = run_cmd or self._subprocess

    @staticmethod
    def _subprocess(argv, env, timeout):
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env,
                              stdin=subprocess.DEVNULL)

    def _record(self, obs: Observation, command: str | None, *, message: str | None,
                invalid: bool, mutating: bool, usage: dict | None) -> Observation:
        self.trace.add(type="action", step=self.steps, kind=obs.kind, command=command,
                       assistant_message=message, exit_code=obs.exit_code, stdout=obs.stdout,
                       stderr=obs.stderr, truncated=obs.truncated, duration_ms=obs.duration_ms,
                       invalid=invalid, mutating=mutating, usage=usage)
        return obs

    def _charge(self) -> None:
        if time.monotonic() > self.deadline:
            raise BudgetExhausted("wall_clock")
        if self.steps >= self.max_steps:
            raise BudgetExhausted("steps")
        self.steps += 1

    def reject(self, kind: str, text: str, *, command: str | None = None,
               message: str | None = None, usage: dict | None = None) -> Observation:
        """Count a step for something that never reached kubectl."""
        self._charge()
        obs = Observation(kind, None, "", text)
        return self._record(obs, command, message=message, invalid=True, mutating=False, usage=usage)

    def run(self, command: str, *, message: str | None = None,
            usage: dict | None = None) -> Observation:
        self._charge()
        try:
            argv = shlex.split(command)
        except ValueError as e:
            return self._record(Observation("policy_rejected", None, "", f"Could not parse command: {e}"),
                                command, message=message, invalid=True, mutating=False, usage=usage)
        if argv and argv[0] == "kubectl":
            argv = argv[1:]
        else:
            return self._record(
                Observation("policy_rejected", None, "", "Only kubectl is available. "
                            "Start the command with 'kubectl'."),
                command, message=message, invalid=True, mutating=False, usage=usage)
        bad = [a for a in argv if a in SHELL_TOKENS]
        if bad:
            return self._record(
                Observation("policy_rejected", None, "",
                            f"Shell syntax ({bad[0]!r}) is not supported; run one plain kubectl command."),
                command, message=message, invalid=True, mutating=False, usage=usage)
        flag = next((a for a in argv for f in FORBIDDEN_FLAGS if a == f or a.startswith(f + "=")), None)
        if flag:
            return self._record(
                Observation("policy_rejected", None, "", f"Flag {flag.split('=')[0]} is not allowed."),
                command, message=message, invalid=True, mutating=False, usage=usage)

        mutating_cmd, _ = classify_command(argv)
        t0 = time.monotonic()
        timeout = max(1, min(self.per_action_timeout_s, int(self.deadline - t0) + 1))
        try:
            r = self._run([str(config.KUBECTL), *argv], base_env(self.kubeconfig), timeout)
            out, err, code, kind = r.stdout, r.stderr, r.returncode, ("ok" if r.returncode == 0 else "exec_error")
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            err = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            code, kind = None, "timeout"
        dur = int((time.monotonic() - t0) * 1000)
        truncated = False
        if len(out) > self.max_output_bytes:
            out, truncated = out[: self.max_output_bytes], True
        if len(err) > self.max_output_bytes:
            err, truncated = err[: self.max_output_bytes], True
        invalid = kind == "exec_error" and any(p in err.lower() for p in INVALID_STDERR_PATTERNS)
        obs = Observation(kind, code, out, err, truncated, dur)
        return self._record(obs, command, message=message, invalid=invalid,
                            mutating=mutating_cmd and kind == "ok", usage=usage)
