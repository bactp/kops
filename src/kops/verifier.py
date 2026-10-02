"""Deterministic verifier: evaluates criteria.yaml against cluster state as verifier-admin.

Tri-state per criterion: pass | fail | error. `error` means the verifier or the
infrastructure failed and makes the trial INVALID; it is never an agent outcome.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field

from . import config

PASS, FAIL, ERROR = "pass", "fail", "error"


@dataclass
class CriterionResult:
    id: str
    invariant: str
    required: bool
    status: str
    evidence: str
    attempts: int = 1
    failure_class: str | None = None


class CheckError(Exception):
    pass


def _get_json(cluster, *args: str) -> dict:
    r = cluster.kubectl(*args, "-o", "json")
    if r.returncode:
        if "NotFound" in r.stderr or "not found" in r.stderr:
            raise LookupError(r.stderr.strip())
        raise CheckError(r.stderr.strip()[-300:])
    return json.loads(r.stdout)


def _walk(obj, path: str):
    """Tiny dotted-path accessor: '.spec.template' -> obj['spec']['template']."""
    cur = obj
    for part in [p for p in path.split(".") if p]:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _resource_args(res: dict) -> list[str]:
    ns = ["-n", res["namespace"]] if res.get("namespace") else []
    return [*ns, "get", res["kind"].lower(), res["name"]]


# -- checks: each returns (status, evidence) ------------------------------------------
def check_endpoints(cluster, c: dict, _ctx) -> tuple[str, str]:
    r = cluster.kubectl("-n", c["namespace"], "get", "endpointslices", "-l",
                        f"kubernetes.io/service-name={c['service']}", "-o", "json")
    if r.returncode:
        raise CheckError(r.stderr.strip()[-300:])
    ready = 0
    for sl in json.loads(r.stdout)["items"]:
        ports = {p.get("port") for p in sl.get("ports") or []}
        if "port" in c and c["port"] not in ports:
            continue
        ready += sum(1 for e in sl.get("endpoints") or []
                     if (e.get("conditions") or {}).get("ready", True))
    ok = ready >= c["min_ready"]
    return (PASS if ok else FAIL), f"ready endpoints on port {c.get('port')}: {ready} (need {c['min_ready']})"


def check_http(cluster, c: dict, _ctx) -> tuple[str, str]:
    ns, pod = c["from"]["namespace"], config.PROBE_POD
    url, attempts = c["url"], c.get("attempts", 1)
    want_reachable = c.get("expect", "reachable") == "reachable"
    results = []
    for _ in range(attempts):
        r = cluster.kubectl("-n", ns, "exec", pod, "--", "wget", "-q", "-O", "/dev/null",
                            "-T", str(c.get("timeout_seconds", 3)), url, timeout=30)
        if r.returncode == 0:
            results.append(True)
        elif "command terminated with exit code" in r.stderr:
            results.append(False)   # wget ran and failed: the target is unreachable
        else:
            raise CheckError(f"probe could not run: {r.stderr.strip()[-200:]}")
    reachable = all(results) if want_reachable else not any(results)
    return (PASS if reachable else FAIL), f"{url}: {results}"


def check_unchanged(cluster, c: dict, ctx) -> tuple[str, str]:
    try:
        obj = _get_json(cluster, *_resource_args(c["resource"]))
    except LookupError as e:
        return FAIL, f"resource missing: {e}"
    vals = {p: _walk(obj, p) for p in c["jsonpaths"]}
    digest = hashlib.sha256(json.dumps(vals, sort_keys=True).encode()).hexdigest()
    ctx_key = ("baseline", c["_cid"])
    if ctx.get("capture"):
        ctx[ctx_key] = digest
        return PASS, "baseline captured"
    base = ctx.get(ctx_key)
    if base is None:
        raise CheckError("no baseline captured for guard")
    return (PASS if digest == base else FAIL), ("unchanged" if digest == base else "changed vs post-setup baseline")


def check_field(cluster, c: dict, _ctx) -> tuple[str, str]:
    try:
        obj = _get_json(cluster, *_resource_args(c["resource"]))
    except LookupError as e:
        return FAIL, f"resource missing: {e}"
    val = _walk(obj, c["path"])
    op, want = c.get("op", "eq"), c.get("value")
    ok = {"eq": val == want, "ne": val != want, "exists": val is not None,
          "gte": val is not None and val >= want}.get(op)
    if ok is None:
        raise CheckError(f"unsupported operator {op!r}")
    return (PASS if ok else FAIL), f"{c['path']}={val!r} {op} {want!r}"


def check_rollout(cluster, c: dict, _ctx) -> tuple[str, str]:
    try:
        d = _get_json(cluster, "-n", c["namespace"], "get", "deployment", c["name"])
    except LookupError as e:
        return FAIL, f"deployment missing: {e}"
    spec, st = d["spec"], d.get("status", {})
    want = spec.get("replicas", 1)
    ok = (st.get("observedGeneration", 0) >= d["metadata"]["generation"]
          and st.get("updatedReplicas", 0) == want and st.get("readyReplicas", 0) == want
          and st.get("replicas", 0) == want)
    return (PASS if ok else FAIL), f"replicas={st.get('replicas')} updated={st.get('updatedReplicas')} ready={st.get('readyReplicas')} want={want}"


CHECKS = {"k8s.endpoints": check_endpoints, "net.http": check_http,
          "k8s.unchanged": check_unchanged, "k8s.field": check_field,
          "k8s.rollout_complete": check_rollout}


class Verifier:
    def __init__(self, cluster, criteria: list[dict], settle: dict | None = None):
        self.cluster, self.criteria = cluster, criteria
        self.settle = settle or {"max_wait_seconds": 0, "poll_interval_seconds": 1}
        self.ctx: dict = {}

    def _once(self, crit: dict) -> tuple[str, str]:
        check = dict(crit["check"], _cid=crit["id"])
        fn = CHECKS.get(check["type"])
        if fn is None:
            return ERROR, f"unsupported check type {check['type']!r}"
        try:
            return fn(self.cluster, check, self.ctx)
        except CheckError as e:
            return ERROR, str(e)
        except Exception as e:  # verifier bug or infra: never an agent failure
            return ERROR, f"{type(e).__name__}: {e}"

    def capture_baselines(self) -> None:
        self.ctx["capture"] = True
        try:
            for c in self.criteria:
                if c["check"]["type"] == "k8s.unchanged":
                    st, ev = self._once(c)
                    if st != PASS:
                        raise CheckError(f"baseline for {c['id']} failed: {ev}")
        finally:
            self.ctx["capture"] = False

    def evaluate(self, only_invariants: list[str] | None = None, *, settle: bool = True
                 ) -> list[CriterionResult]:
        """Evaluate criteria. Criteria marked `settle` are re-polled together until they all
        pass or one shared deadline (verification.settle.max_wait_seconds) expires."""
        crits = [c for c in self.criteria
                 if only_invariants is None or c["invariant"] in only_invariants]
        done: dict[str, tuple[str, str]] = {}
        attempts = {c["id"]: 0 for c in crits}
        pending = crits
        deadline = time.monotonic() + (self.settle["max_wait_seconds"] if settle else 0)
        while True:
            retry = []
            for c in pending:
                attempts[c["id"]] += 1
                done[c["id"]] = self._once(c)
                if done[c["id"]][0] == FAIL and settle and c.get("settle"):
                    retry.append(c)
            pending = retry
            if not pending or time.monotonic() >= deadline:
                break
            time.sleep(self.settle["poll_interval_seconds"])
        return [CriterionResult(c["id"], c["invariant"], c.get("required", True), *done[c["id"]],
                                attempts[c["id"]], c.get("failure_class")) for c in crits]

    @staticmethod
    def outcome(results: list[CriterionResult]) -> str:
        if any(r.status == ERROR for r in results):
            return "INVALID"
        return "PASS" if all(r.status == PASS for r in results if r.required) else "FAIL"
