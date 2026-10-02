"""Model backends. Lightweight on purpose: the research target is the agent."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class ModelError(Exception):
    """The model endpoint failed. Not attributable to the model's behaviour."""


@dataclass
class Reply:
    text: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    latency_s: float = 0.0


class ChatModel(Protocol):
    def describe(self) -> dict: ...
    def generate(self, messages: list[dict]) -> Reply: ...


class OpenAICompatModel:
    """Any OpenAI-compatible /chat/completions endpoint (vLLM, Ollama, frontier APIs)."""

    def __init__(self, model: str, base_url: str, api_key_env: str | None = None,
                 temperature: float = 0.0, max_tokens: int = 1024, seed: int | None = None,
                 timeout_s: int = 120, retries: int = 2):
        self.model, self.base_url = model, base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.params = {"temperature": temperature, "max_tokens": max_tokens}
        if seed is not None:
            self.params["seed"] = seed
        self.timeout_s, self.retries = timeout_s, retries
        self.served_id: str | None = None

    def describe(self) -> dict:
        return {"provider": "openai-compatible", "id": self.model, "served_id": self.served_id,
                "endpoint": self.base_url, "params": dict(self.params), "weights_ref": None}

    def generate(self, messages: list[dict]) -> Reply:
        body = json.dumps({"model": self.model, "messages": messages, **self.params}).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key_env:
            key = os.environ.get(self.api_key_env)
            if not key:
                raise ModelError(f"environment variable {self.api_key_env} is not set")
            headers["Authorization"] = f"Bearer {key}"
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            t0 = time.monotonic()
            try:
                req = urllib.request.Request(f"{self.base_url}/chat/completions", body, headers)
                with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
                    data = json.load(r)
                self.served_id = data.get("model", self.served_id)
                usage = data.get("usage") or {}
                return Reply(data["choices"][0]["message"]["content"] or "",
                             usage.get("prompt_tokens"), usage.get("completion_tokens"),
                             time.monotonic() - t0)
            except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
                last = e
                time.sleep(1 + attempt)
        raise ModelError(f"model call failed after {self.retries + 1} attempts: {last}")


class ScriptedModel:
    """Returns canned replies. Used to test the harness without a real model."""

    def __init__(self, replies: list[str], name: str = "scripted"):
        self._replies, self._i, self.name = replies, 0, name

    def describe(self) -> dict:
        return {"provider": "scripted", "id": self.name, "served_id": None,
                "endpoint": None, "params": {}, "weights_ref": None}

    def generate(self, messages: list[dict]) -> Reply:
        text = self._replies[min(self._i, len(self._replies) - 1)]
        self._i += 1
        return Reply(text, 0, 0, 0.0)
