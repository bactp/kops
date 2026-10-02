"""Derived metrics and the trial record. Metrics come only from the trace."""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA = "kops-result/v0"


def derive_metrics(events: list[dict], wall_seconds: float) -> dict:
    acts = [e for e in events if e["type"] == "action"]
    by_kind = {k: sum(1 for a in acts if a["kind"] == k)
               for k in ("ok", "exec_error", "timeout", "policy_rejected", "parse_error")}
    invalid = sum(1 for a in acts if a["invalid"])
    errors = [a for a in acts if a["kind"] != "ok"]
    # Recovery (heuristic): an error step whose next step succeeded.
    recov = 0
    for i, a in enumerate(acts[:-1]):
        if a["kind"] != "ok" and acts[i + 1]["kind"] == "ok":
            recov += 1
    usage = [a.get("usage") or {} for a in acts if a.get("usage")]
    usage += [e.get("usage") or {} for e in events if e["type"] == "submit"]
    tin = sum(u.get("tokens_in") or 0 for u in usage)
    tout = sum(u.get("tokens_out") or 0 for u in usage)
    return {
        "steps": len(acts), "commands": by_kind["ok"] + by_kind["exec_error"] + by_kind["timeout"],
        "executable_command_rate": (by_kind["ok"] / len(acts)) if acts else None,
        "invalid_actions": invalid, "exec_errors": by_kind["exec_error"],
        "timeouts": by_kind["timeout"], "policy_rejected": by_kind["policy_rejected"],
        "parse_errors": by_kind["parse_error"],
        "mutating_steps": sum(1 for a in acts if a["mutating"]),
        "had_error": bool(errors), "recovery_count": recov,
        "wall_seconds": round(wall_seconds, 2),
        "model_seconds": round(sum(u.get("latency_s") or 0 for u in usage), 2),
        "tokens_in": tin, "tokens_out": tout,
    }


def auto_failure_labels(outcome: str, metrics: dict, termination: str) -> list[str]:
    """Labels derivable from the trace. Knowledge/reasoning are NOT auto-labelled."""
    if outcome != "FAIL":
        return []
    labels = []
    if metrics["parse_errors"] or metrics["policy_rejected"]:
        labels.append("tool_use")
    if metrics["invalid_actions"] - metrics["parse_errors"] - metrics["policy_rejected"] > 0:
        labels.append("execution")
    if metrics["mutating_steps"] == 0:
        labels.append("no_attempt")
    if metrics["had_error"]:
        labels.append("recovery_not_achieved")
    if termination.startswith("budget"):
        labels.append("budget_exhausted")
    return labels


def write_trial(dirpath: Path, record: dict) -> None:
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "trial.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
