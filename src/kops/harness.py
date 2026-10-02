"""Agents: null, oracle (scripted), and the model-driven shell loop (Reference Scaffold v0).

An agent runs until it submits or a budget is exhausted. It only ever touches the
cluster through the Gateway.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .gateway import BudgetExhausted, Gateway
from .models import ChatModel, ModelError

PROMPT_VERSION = "p1"
SYSTEM_PROMPT = """You are an operator working on a Kubernetes cluster through a terminal.
Only `kubectl` is available. Your task is given in the first message.

Reply with exactly ONE of the following in every message:
1. A single kubectl command in a fenced code block:
```bash
kubectl get pods
```
2. A line starting with `SUBMIT:` followed by a one-sentence summary, when you believe the task is done.

Rules:
- One plain kubectl command per message. No pipes, redirects, `&&`, or shell syntax.
- No interactive commands (no `kubectl edit`, no `exec -it`); there is no TTY or stdin.
  Use `patch`, `set`, `scale`, `label`, `annotate`, `create`, `delete`, `rollout`, etc.
- You see each command's exit code, stdout and stderr. If a command fails, read the error and adjust.
- Inspect the cluster before changing it, and check the result after changing it."""
PROMPT_SHA256 = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()

_FENCE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.S)


def parse_reply(text: str) -> tuple[str, str]:
    """-> (kind, payload): ('command', cmd) | ('submit', summary) | ('malformed', reason)."""
    m = _FENCE.search(text)
    if m:
        lines = [l.strip() for l in m.group(1).strip().splitlines() if l.strip()]
        if len(lines) == 1:
            return "command", lines[0]
        return "malformed", f"expected exactly one command in the code block, got {len(lines)} lines"
    for line in text.splitlines():
        if line.strip().upper().startswith("SUBMIT:"):
            return "submit", line.strip()[7:].strip()
    return "malformed", "reply contained neither a fenced kubectl command nor a SUBMIT: line"


@dataclass
class AgentOutcome:
    termination: str            # submitted | budget_steps | budget_wall_clock | no_action
    claim: str | None = None


class NullAgent:
    name = "null"

    def describe(self) -> dict:
        return {"name": self.name, "model": None,
                "harness": {"name": "null", "version": "1", "prompt_version": None,
                            "prompt_sha256": None, "tools": []}}

    def run(self, task: str, gw: Gateway) -> AgentOutcome:
        return AgentOutcome("no_action")


class ScriptedAgent:
    """Replays a fixed command list through the gateway (oracle / negative solutions)."""

    def __init__(self, name: str, commands: list[str]):
        self.name, self.commands = name, commands

    def describe(self) -> dict:
        return {"name": self.name, "model": None,
                "harness": {"name": "scripted", "version": "1", "prompt_version": None,
                            "prompt_sha256": None, "tools": ["kubectl"]}}

    def run(self, task: str, gw: Gateway) -> AgentOutcome:
        try:
            for cmd in self.commands:
                gw.run(cmd)
        except BudgetExhausted as e:
            return AgentOutcome(f"budget_{e.reason}")
        return AgentOutcome("submitted", "scripted replay finished")


class ShellLoopAgent:
    """Reference scaffold: observe -> model -> one kubectl command -> observe, full history."""

    def __init__(self, name: str, model: ChatModel):
        self.name, self.model = name, model

    def describe(self) -> dict:
        return {"name": self.name, "model": self.model.describe(),
                "harness": {"name": "shell-loop", "version": "0.1", "prompt_version": PROMPT_VERSION,
                            "prompt_sha256": PROMPT_SHA256, "tools": ["kubectl"]}}

    def run(self, task: str, gw: Gateway) -> AgentOutcome:
        history = [{"role": "system", "content": SYSTEM_PROMPT},
                   {"role": "user", "content": task}]
        try:
            while True:
                reply = self.model.generate(history)   # ModelError propagates -> INVALID
                usage = {"tokens_in": reply.tokens_in, "tokens_out": reply.tokens_out,
                         "latency_s": round(reply.latency_s, 3)}
                kind, payload = parse_reply(reply.text)
                history.append({"role": "assistant", "content": reply.text})
                if kind == "submit":
                    gw.trace.add(type="submit", assistant_message=reply.text, usage=usage, claim=payload)
                    return AgentOutcome("submitted", payload)
                if kind == "malformed":
                    obs = gw.reject("parse_error", "Reply not understood: " + payload +
                                    ". Send one kubectl command in a ```bash block, or `SUBMIT: ...`.",
                                    message=reply.text, usage=usage)
                else:
                    obs = gw.run(payload, message=reply.text, usage=usage)
                history.append({"role": "user", "content": obs.render()})
        except BudgetExhausted as e:
            gw.trace.add(type="budget_exhausted", reason=e.reason)
            return AgentOutcome(f"budget_{e.reason}")


__all__ = ["NullAgent", "ScriptedAgent", "ShellLoopAgent", "AgentOutcome", "ModelError", "parse_reply"]
