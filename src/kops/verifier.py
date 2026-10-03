"""Deterministic verifier: evaluates criteria.yaml against cluster state as verifier-admin.

Tri-state per criterion: pass | fail | error. `error` means the verifier or the
infrastructure failed and makes the trial INVALID; it is never an agent outcome.
"""
from __future__ import annotations

import hashlib
import json
import re
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


# -- JSONPath-like accessor ---------------------------------------------------------
_TOK = re.compile(r"""
    \.(?P<key>[A-Za-z0-9_\-/]+)                      # .key
  | \[(?P<idx>-?\d+)\]                               # [0]
  | \[(?P<star>\*)\]                                 # [*]
  | \[\?\(@\.(?P<fpath>[A-Za-z0-9_.\-/]+)\s*(?P<fop>==|!=)\s*(?P<fval>"[^"]*"|'[^']*'|[^\)\s]+)\)\]
  | \[(?P<q>"[^"]*"|'[^']*')\]                       # ['a.b']
""", re.X)


def _literal(txt: str):
    if txt[0] in "\"'":
        return txt[1:-1]
    if txt in ("true", "false"):
        return txt == "true"
    if txt == "null":
        return None
    try:
        return int(txt)
    except ValueError:
        return txt


def parse_path(path: str) -> list[tuple]:
    toks, pos = [], 0
    path = path.strip()
    if path and path[0] not in ".[":
        path = "." + path
    while pos < len(path):
        m = _TOK.match(path, pos)
        if not m:
            raise CheckError(f"unsupported path syntax at {path[pos:]!r} in {path!r}")
        pos = m.end()
        if m.group("key") is not None:
            toks.append(("key", m.group("key")))
        elif m.group("idx") is not None:
            toks.append(("idx", int(m.group("idx"))))
        elif m.group("star"):
            toks.append(("star",))
        elif m.group("q") is not None:
            toks.append(("key", m.group("q")[1:-1]))
        else:
            toks.append(("filter", m.group("fpath"), m.group("fop"), _literal(m.group("fval"))))
    return toks


def select(obj, path: str) -> tuple[list, bool]:
    """-> (values, multi). `multi` is True when the path contains [*] or a filter.
    A missing key contributes no value (a single-valued path returns [])."""
    cur, multi = [obj], False
    for tok in parse_path(path):
        nxt = []
        for o in cur:
            if tok[0] == "key":
                if isinstance(o, dict) and tok[1] in o:
                    nxt.append(o[tok[1]])
            elif tok[0] == "idx":
                if isinstance(o, list) and -len(o) <= tok[1] < len(o):
                    nxt.append(o[tok[1]])
            elif tok[0] == "star":
                multi = True
                if isinstance(o, list):
                    nxt.extend(o)
                elif isinstance(o, dict):
                    nxt.extend(o.values())
            else:
                multi = True
                _, fpath, fop, fval = tok
                for it in (o if isinstance(o, list) else []):
                    got, _m = select(it, fpath)
                    v = got[0] if got else None
                    if (v == fval) == (fop == "=="):
                        nxt.append(it)
        cur = nxt
    return cur, multi


def _walk(obj, path: str):
    """Single value or None (kept for callers that only need one value)."""
    vals, multi = select(obj, path)
    if not vals:
        return None
    return vals if multi else vals[0]


_QTY = {"n": 1e-9, "u": 1e-6, "m": 1e-3, "": 1, "k": 1e3, "M": 1e6, "G": 1e9, "T": 1e12,
        "P": 1e15, "E": 1e18, "Ki": 2**10, "Mi": 2**20, "Gi": 2**30, "Ti": 2**40, "Pi": 2**50,
        "Ei": 2**60}


def quantity(v) -> float:
    """Kubernetes resource.Quantity -> float (cpu in cores, memory in bytes)."""
    m = re.fullmatch(r"([0-9.]+)([A-Za-z]*)", str(v).strip())
    if not m or m.group(2) not in _QTY:
        raise CheckError(f"not a quantity: {v!r}")
    return float(m.group(1)) * _QTY[m.group(2)]


def _op(op: str, val, want) -> bool:
    if op == "exists":
        return val is not None
    if op == "absent":
        return val is None
    if op == "eq":
        return val == want
    if op == "ne":
        return val != want
    if val is None:
        return False
    if op == "in":
        return val in want
    if op == "not_in":
        return val not in want
    if op == "regex":
        return re.search(want, str(val)) is not None
    if op == "gte":
        return val >= want
    if op == "lte":
        return val <= want
    if op == "contains":
        return want in val
    if op == "subset":
        return isinstance(val, dict) and all(val.get(k) == v for k, v in want.items())
    if op in ("qty_eq", "qty_gte", "qty_lte"):
        a, b = quantity(val), quantity(want)
        return {"qty_eq": a == b, "qty_gte": a >= b, "qty_lte": a <= b}[op]
    raise CheckError(f"unsupported operator {op!r}")


def _kind(res: dict) -> str:
    return res["kind"].lower()


def _fetch(cluster, res: dict) -> list[dict]:
    """Objects addressed by a resource ref: by name, by label selector, or all of a kind."""
    ns = ["-n", res["namespace"]] if res.get("namespace") else []
    if res.get("name"):
        try:
            return [_get_json(cluster, *ns, "get", _kind(res), res["name"])]
        except LookupError:
            return []
    sel = ["-l", res["selector"]] if res.get("selector") else []
    r = cluster.kubectl(*ns, "get", _kind(res), *sel, "-o", "json")
    if r.returncode:
        raise CheckError(r.stderr.strip()[-300:])
    return json.loads(r.stdout).get("items", [])


def _resource_args(res: dict) -> list[str]:
    ns = ["-n", res["namespace"]] if res.get("namespace") else []
    return [*ns, "get", _kind(res), res["name"]]


def _describe(res: dict) -> str:
    return f"{res['kind']}/{res.get('name') or res.get('selector') or '*'}"


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


def _probe_target(cluster, frm: dict) -> tuple[list[str], str]:
    """-> (kubectl exec prefix, label). Default: the verifier-owned probe pod."""
    ns = frm["namespace"]
    if frm.get("pod"):
        pod = frm["pod"]
    elif frm.get("labels"):
        sel = ",".join(f"{k}={v}" for k, v in sorted(frm["labels"].items()))
        r = cluster.kubectl("-n", ns, "get", "pods", "-l", sel, "-o", "json")
        if r.returncode:
            raise CheckError(r.stderr.strip()[-300:])
        pods = [p for p in json.loads(r.stdout)["items"]
                if p["status"].get("phase") == "Running" and not p["metadata"].get("deletionTimestamp")]
        if not pods:
            raise LookupError(f"no running client pod with labels {sel} in {ns}")
        pod = sorted(p["metadata"]["name"] for p in pods)[0]
    else:
        pod = config.PROBE_POD
    pre = ["-n", ns, "exec", pod]
    if frm.get("container"):
        pre += ["-c", frm["container"]]
    return pre, f"{ns}/{pod}"


def _exec(cluster, frm: dict, argv: list[str]):
    """Run a probe command; -> (returncode, stdout, stderr). Raises CheckError if the probe itself cannot run."""
    pre, _ = _probe_target(cluster, frm)
    r = cluster.kubectl(*pre, "--", *argv, timeout=40)
    if r.returncode and "command terminated with exit code" not in r.stderr:
        raise CheckError(f"probe could not run: {r.stderr.strip()[-200:]}")
    return r.returncode, r.stdout, r.stderr


def check_http(cluster, c: dict, _ctx) -> tuple[str, str]:
    url, attempts = c["url"], c.get("attempts", 1)
    want_reachable = c.get("expect", "reachable") == "reachable"
    results, notes = [], []
    for _ in range(attempts):
        try:
            rc, out, err = _exec(cluster, c["from"], ["wget", "-q", "-S", "-O", "-", "-T",
                                                      str(c.get("timeout_seconds", 3)), url])
        except LookupError as e:
            if want_reachable:
                return FAIL, str(e)
            results.append(False)
            continue
        codes = re.findall(r"HTTP/\d(?:\.\d)? (\d{3})", err)
        status = int(codes[-1]) if codes else (200 if rc == 0 else None)
        ok = rc == 0
        if ok and "status" in c and status != c["status"]:
            ok = False
        if ok and c.get("body_regex") and not re.search(c["body_regex"], out):
            ok = False
        if not ok and rc == 0:
            notes.append(f"status={status} body={out[:60]!r}")
        results.append(ok)
    reachable = all(results) if want_reachable else not any(results)
    return (PASS if reachable else FAIL), f"{url}: {results} {' '.join(notes[:1])}".strip()


def check_tcp(cluster, c: dict, _ctx) -> tuple[str, str]:
    want_reachable = c.get("expect", "reachable") == "reachable"
    results = []
    for _ in range(c.get("attempts", 1)):
        try:
            rc, _o, _e = _exec(cluster, c["from"], ["nc", "-z", "-w", str(c.get("timeout_seconds", 3)),
                                                    c["host"], str(c["port"])])
        except LookupError as e:
            if want_reachable:
                return FAIL, str(e)
            rc = 1
        results.append(rc == 0)
    ok = all(results) if want_reachable else not any(results)
    return (PASS if ok else FAIL), f"{c['host']}:{c['port']}: {results}"


def check_dns(cluster, c: dict, _ctx) -> tuple[str, str]:
    try:
        rc, out, err = _exec(cluster, c["from"], ["nslookup", c["name"]])
    except LookupError as e:
        return FAIL, str(e)
    text = out + err
    answered = rc == 0 and re.search(r"^Address(?: \d+)?: ", text.split("Name:", 1)[-1], re.M) is not None \
        and "NXDOMAIN" not in text
    if c["expect"] == "nxdomain":
        return (PASS if not answered else FAIL), f"{c['name']}: {'resolves' if answered else 'no answer'}"
    ok = answered and (not c.get("answer_regex") or re.search(c["answer_regex"], text) is not None)
    return (PASS if ok else FAIL), f"{c['name']}: {'resolves' if answered else 'no answer'}"


def check_unchanged(cluster, c: dict, ctx) -> tuple[str, str]:
    try:
        obj = _get_json(cluster, *_resource_args(c["resource"]))
    except LookupError as e:
        return FAIL, f"resource missing: {e}"
    paths = c.get("jsonpaths") or {"spec": [".spec"], "spec+metadata.labels": [".spec", ".metadata.labels"],
                                   "data": [".data"]}.get(c["scope"], [])
    vals = {p: select(obj, p)[0] for p in paths}
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
    path = c.get("jsonpath") or c.get("path")
    op, want = c["op"] if "op" in c else "eq", c.get("value")
    items = _fetch(cluster, c["resource"])
    if not items:
        return FAIL, f"resource missing: {_describe(c['resource'])}"
    if "value_from" in c:   # expected value computed from another live object (diagnosis tasks)
        vf = c["value_from"]
        src = _fetch(cluster, vf["resource"])
        got, _m = select(src[0], vf["jsonpath"]) if src else ([], False)
        if not got:
            raise CheckError(f"reference value missing: {_describe(vf['resource'])} {vf['jsonpath']}")
        want = got[0]
    vals: list = []
    for obj in items:
        got, multi = select(obj, path)
        vals.extend(got if got else [None])
    results = [_op(op, v, want) for v in vals]
    all_items = c.get("all_items", True)
    ok = all(results) if all_items else any(results)
    return (PASS if ok else FAIL), f"{path}={vals[0] if len(vals) == 1 else vals!r} {op} {want!r}"


def check_exists(cluster, c: dict, _ctx) -> tuple[str, str]:
    n = len(_fetch(cluster, c["resource"]))
    ok = n > 0 if c["expect"] == "present" else n == 0
    return (PASS if ok else FAIL), f"{_describe(c['resource'])}: {n} found, expected {c['expect']}"


def check_count(cluster, c: dict, _ctx) -> tuple[str, str]:
    items = _fetch(cluster, c["resource"])
    if c.get("field_filter"):
        m = re.fullmatch(r"\s*(\S+?)\s*(==|!=)\s*(.+?)\s*", c["field_filter"])
        if not m:
            raise CheckError(f"bad field_filter {c['field_filter']!r}")
        want = _literal(m.group(3))
        def keep(o):
            vals, _ = select(o, m.group(1))
            v = vals[0] if vals else None
            # lenient on scalar type: annotations/labels are strings, so `==true` must match "true"
            same = v == want or (v is not None and str(v).lower() == str(want).lower())
            return same == (m.group(2) == "==")
        items = [o for o in items if keep(o)]
    n = len(items)
    ok = {"eq": n == c["value"], "gte": n >= c["value"], "lte": n <= c["value"]}[c["op"]]
    return (PASS if ok else FAIL), f"count {_describe(c['resource'])} {c.get('field_filter') or ''}: {n} {c['op']} {c['value']}"


def check_condition(cluster, c: dict, _ctx) -> tuple[str, str]:
    items = _fetch(cluster, c["resource"])
    if not items:
        return FAIL, f"resource missing: {_describe(c['resource'])}"
    got = []
    for o in items:
        conds = (o.get("status") or {}).get("conditions") or []
        got.append(next((x.get("status") for x in conds if x.get("type") == c["condition"]), None))
    ok = all(g == c["status"] for g in got)
    return (PASS if ok else FAIL), f"{c['condition']}={got} want {c['status']}"


def check_can_i(cluster, c: dict, _ctx) -> tuple[str, str]:
    args = ["auth", "can-i", c["verb"], c["resource"], f"--as={c['as']}"]
    if c.get("subresource"):
        args.append(f"--subresource={c['subresource']}")
    if c.get("namespace"):
        args += ["-n", c["namespace"]]
    r = cluster.kubectl(*args)
    ans = r.stdout.strip().split("\n")[0].strip() if r.stdout.strip() else ""
    if ans not in ("yes", "no"):
        raise CheckError(f"auth can-i unusable: rc={r.returncode} {(r.stderr or r.stdout).strip()[-200:]}")
    allowed = ans == "yes"
    return (PASS if allowed == (c["expect"] == "allow") else FAIL), \
        f"{c['as']} {c['verb']} {c['resource']} ns={c.get('namespace')}: {ans} (expect {c['expect']})"


def check_logs(cluster, c: dict, _ctx) -> tuple[str, str]:
    res = c["resource"]
    ns = ["-n", res["namespace"]] if res.get("namespace") else []
    target = [f"{_kind(res)}/{res['name']}"] if res.get("name") else ["-l", res["selector"], "--max-log-requests=10"]
    extra = (["-c", c["container"]] if c.get("container") else []) + (["--previous"] if c.get("previous") else []) \
        + ([f"--tail={c['tail']}"] if c.get("tail") else [])
    r = cluster.kubectl(*ns, "logs", *target, *extra)
    if r.returncode:
        if any(t in r.stderr for t in ("connection refused", "Unable to connect", "i/o timeout", "TLS handshake")):
            raise CheckError(r.stderr.strip()[-200:])
        return FAIL, f"logs unavailable: {r.stderr.strip()[-120:]}"
    n = len(re.findall(c["regex"], r.stdout, re.M))
    if c.get("expect", "match") == "match":
        ok = n >= c.get("min_matches", 1)
    else:
        ok = n == 0
    return (PASS if ok else FAIL), f"{n} line(s) match /{c['regex']}/ in logs of {_describe(res)}"


def check_placement(cluster, c: dict, _ctx) -> tuple[str, str]:
    pods = [p for p in _fetch(cluster, {"kind": "Pod", "namespace": c["namespace"], "selector": c["selector"]})
            if p["status"].get("phase") == "Running" and not p["metadata"].get("deletionTimestamp")]
    per: dict[str, int] = {}
    for p in pods:
        per[p["spec"].get("nodeName")] = per.get(p["spec"].get("nodeName"), 0) + 1
    notes = [f"{len(pods)} running pods, per node {per}"]
    ok = len(pods) >= c.get("min_pods", 1)
    if c.get("node_selector"):
        nodes = {n["metadata"]["name"] for n in _fetch(cluster, {"kind": "Node", "selector": c["node_selector"]})}
        inside = all(n in nodes for n in per)
        ok = ok and (inside if c.get("mode", "within") == "within" else not any(n in nodes for n in per))
        notes.append(f"nodes[{c['node_selector']}]={sorted(nodes)} mode={c.get('mode', 'within')}")
    if "max_per_node" in c:
        ok = ok and all(v <= c["max_per_node"] for v in per.values())
    if "min_distinct_nodes" in c:
        ok = ok and len(per) >= c["min_distinct_nodes"]
    return (PASS if ok else FAIL), "; ".join(notes)


def check_rollout(cluster, c: dict, _ctx) -> tuple[str, str]:
    res = c.get("resource") or {"kind": "Deployment", "name": c["name"], "namespace": c["namespace"]}
    items = _fetch(cluster, res)
    if not items:
        return FAIL, f"{res['kind']} missing"
    d = items[0]
    spec, st = d["spec"], d.get("status", {})
    want = spec.get("replicas", 1)
    ok = (st.get("observedGeneration", 0) >= d["metadata"]["generation"]
          and st.get("updatedReplicas", 0) == want and st.get("readyReplicas", 0) == want
          and st.get("replicas", 0) == want)
    return (PASS if ok else FAIL), f"replicas={st.get('replicas')} updated={st.get('updatedReplicas')} ready={st.get('readyReplicas')} want={want}"


def check_stability(cluster, c: dict, ctx) -> tuple[str, str]:
    n, window = c["samples"], c["window_seconds"]
    inner = dict(c["check"], _cid=c["_cid"])
    for i in range(n):
        st, ev = CHECKS[inner["type"]](cluster, inner, ctx)
        if st != PASS:
            return st, f"sample {i + 1}/{n}: {ev}"
        if i < n - 1:
            time.sleep(window / (n - 1))
    return PASS, f"stable over {n} samples in {window}s: {ev}"


CHECKS = {"k8s.endpoints": check_endpoints, "net.http": check_http, "net.tcp": check_tcp,
          "net.dns": check_dns, "k8s.unchanged": check_unchanged, "k8s.field": check_field,
          "k8s.exists": check_exists, "k8s.count": check_count, "k8s.condition": check_condition,
          "k8s.can_i": check_can_i, "k8s.logs": check_logs, "k8s.placement": check_placement,
          "k8s.rollout_complete": check_rollout, "stability": check_stability}


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
