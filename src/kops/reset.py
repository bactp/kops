"""API-level reset: capture a baseline of object state, later delete what a scenario created
and restore what it changed, then require the state digest to equal the baseline.

Works on any object with `.kubectl(*args, input=..., timeout=...)` (a `Sandbox`). Only the
configured kinds are covered; that is the stated guarantee of `reset: api`.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CLUSTER_KINDS = ["namespaces", "storageclasses", "clusterroles", "clusterrolebindings",
                 "priorityclasses", "persistentvolumes"]
NAMESPACED_KINDS = ["configmaps", "serviceaccounts", "deployments", "daemonsets", "statefulsets",
                    "services", "networkpolicies", "roles", "rolebindings", "ingresses",
                    "persistentvolumeclaims", "jobs", "cronjobs", "horizontalpodautoscalers",
                    "poddisruptionbudgets", "secrets"]
# Objects that Kubernetes regenerates on its own and that therefore never count as a change.
IGNORED = {("configmaps", "kube-root-ca.crt")}
_DROP = {"resourceVersion", "uid", "creationTimestamp", "managedFields", "generation", "selfLink",
         "ownerReferences"}
_DROP_ANNOTATIONS = {"kubectl.kubernetes.io/last-applied-configuration",
                     "deployment.kubernetes.io/revision"}

_PLURAL = {"Namespace": "namespaces", "StorageClass": "storageclasses", "ClusterRole": "clusterroles",
           "ClusterRoleBinding": "clusterrolebindings", "PriorityClass": "priorityclasses",
           "PersistentVolume": "persistentvolumes", "ConfigMap": "configmaps", "ServiceAccount": "serviceaccounts",
           "Deployment": "deployments", "DaemonSet": "daemonsets", "StatefulSet": "statefulsets",
           "Service": "services", "NetworkPolicy": "networkpolicies", "Role": "roles",
           "RoleBinding": "rolebindings", "Ingress": "ingresses", "PersistentVolumeClaim": "persistentvolumeclaims",
           "Job": "jobs", "CronJob": "cronjobs", "HorizontalPodAutoscaler": "horizontalpodautoscalers",
           "PodDisruptionBudget": "poddisruptionbudgets", "Secret": "secrets"}

Key = tuple[str, str, str]   # (kind, namespace, name)


def _strip(o):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k in _DROP or k == "status":
                continue
            if k == "annotations" and isinstance(v, dict):
                v = {a: b for a, b in v.items() if a not in _DROP_ANNOTATIONS}
                if not v:
                    continue
            out[k] = _strip(v)
        return out
    if isinstance(o, list):
        return [_strip(x) for x in o]
    return o


def digest_of(objs: dict[Key, dict]) -> str:
    blob = json.dumps({"|".join(k): v for k, v in sorted(objs.items())}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


@dataclass
class Baseline:
    objects: dict[Key, dict]
    digest: str = ""

    def __post_init__(self):
        self.digest = self.digest or digest_of(self.objects)

    def to_json(self) -> str:
        return json.dumps({"digest": self.digest, "objects": {"|".join(k): v for k, v in self.objects.items()}})

    @classmethod
    def from_json(cls, text: str) -> "Baseline":
        d = json.loads(text)
        return cls({tuple(k.split("|", 2)): v for k, v in d["objects"].items()}, d["digest"])  # type: ignore[misc]


@dataclass
class ResetReport:
    deleted: int = 0
    restored: int = 0
    errors: list[str] = field(default_factory=list)


class Reset:
    def __init__(self, cluster, cluster_kinds: list[str] | None = None,
                 namespaced_kinds: list[str] | None = None, ignored: set | None = None):
        self.cluster = cluster
        self.cluster_kinds = list(CLUSTER_KINDS if cluster_kinds is None else cluster_kinds)
        self.namespaced_kinds = list(NAMESPACED_KINDS if namespaced_kinds is None else namespaced_kinds)
        self.ignored = IGNORED if ignored is None else ignored

    def _add(self, objs: dict, kind: str, it: dict) -> None:
        md = it["metadata"]
        if (kind, md["name"]) in self.ignored:
            return
        obj = _strip(it)
        if kind == "secrets":   # never keep secret material: track presence and a hash only
            obj = {"__sha__": hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()}
        if md.get("deletionTimestamp"):
            obj["__terminating__"] = True
        objs[(kind, md.get("namespace", ""), md["name"])] = obj

    def _collect_combined(self, kinds: list[str]) -> dict[Key, dict] | None:
        """One kubectl call for every kind (about 6x faster than one call per kind); None if it fails."""
        r = self.cluster.kubectl("get", ",".join(kinds), "-A", "-o", "json", timeout=90)
        if r.returncode:
            return None
        objs: dict[Key, dict] = {}
        for it in json.loads(r.stdout).get("items", []):
            kind = _PLURAL.get(it.get("kind", ""))
            if kind is None or kind not in kinds:
                return None
            self._add(objs, kind, it)
        return objs

    def collect(self) -> dict[Key, dict]:
        kinds = self.cluster_kinds + self.namespaced_kinds
        if getattr(self.cluster, "multi_get", False) and set(kinds) <= set(_PLURAL.values()):
            objs = self._collect_combined(kinds)
            if objs is not None:
                return objs
        objs = {}
        for kind in kinds:
            scope = [] if kind in self.cluster_kinds else ["-A"]
            r = self.cluster.kubectl("get", kind, *scope, "-o", "json", timeout=60)
            if r.returncode:   # kind not served by this cluster: nothing to track
                continue
            for it in json.loads(r.stdout).get("items", []):
                self._add(objs, kind, it)
        return objs

    def capture_baseline(self) -> Baseline:
        return Baseline(self.collect())

    def digest(self) -> str:
        return digest_of(self.collect())

    def reset(self, base: Baseline, cur: dict | None = None) -> ResetReport:
        """One pass: delete extra objects, put back changed or removed ones. `cur` is a fresh `collect()`."""
        rep = ResetReport()
        cur = self.collect() if cur is None else cur
        extra = [k for k in cur if k not in base.objects and not cur[k].get("__terminating__")]
        for key in extra:       # namespaces first: their contents go with them
            if key[0] == "namespaces":
                self._delete(key, rep)
        gone_ns = {k[2] for k in extra if k[0] == "namespaces"}
        for key in extra:
            if key[0] != "namespaces" and key[1] not in gone_ns:
                self._delete(key, rep)
        order = sorted(base.objects, key=lambda k: (k[0] != "namespaces", k))
        for key in order:
            want = base.objects[key]
            if cur.get(key) != want:
                self._restore(key, want, key in cur, rep)
        return rep

    def wait_restored(self, base: Baseline, timeout: float = 120, interval: float = 2,
                      passes: int = 3) -> bool:
        """Repeat `reset` until the digest equals the baseline or the timeout expires."""
        deadline = time.monotonic() + timeout
        n = 0
        while True:
            cur = self.collect()
            if digest_of(cur) == base.digest:
                return True
            if time.monotonic() >= deadline:
                return False
            if n < passes or n % 5 == 0:
                self.reset(base, cur)
            n += 1
            time.sleep(interval)

    # -- helpers ---------------------------------------------------------------------------
    def _delete(self, key: Key, rep: ResetReport) -> None:
        kind, ns, name = key
        if kind == "namespaces" and getattr(self.cluster, "multi_get", False):
            # a namespace stays Terminating until its pods are gone (30 s of grace for a pod that ignores SIGTERM):
            # remove them at once, there is nothing to preserve in a scenario's own namespace
            self.cluster.kubectl("delete", "pods", "--all", "-n", name, "--grace-period=0", "--force",
                                 "--wait=false", "--ignore-not-found", timeout=60)
        args = ["delete", kind, name, "--wait=false", "--ignore-not-found"] + (["-n", ns] if ns else [])
        r = self.cluster.kubectl(*args, timeout=60)
        if r.returncode:
            rep.errors.append(f"delete {kind}/{name}: {r.stderr.strip()[-200:]}")
        else:
            rep.deleted += 1

    def _restore(self, key: Key, want: dict, exists: bool, rep: ResetReport) -> None:
        if "__sha__" in want:
            rep.errors.append(f"cannot restore {key[0]}/{key[2]}: contents not stored")
            return
        obj = {k: v for k, v in want.items() if k != "__terminating__"}
        doc = json.dumps(obj)
        if exists:
            r = self.cluster.kubectl("replace", "-f", "-", input=doc, timeout=60)
            if r.returncode and key[0] != "namespaces":   # never force-replace a namespace
                r = self.cluster.kubectl("replace", "--force", "-f", "-", input=doc, timeout=60)
            if r.returncode:
                r = self.cluster.kubectl("apply", "-f", "-", input=doc, timeout=60)
        else:
            r = self.cluster.kubectl("create", "-f", "-", input=doc, timeout=60)
        if r.returncode:
            rep.errors.append(f"restore {key[0]}/{key[2]}: {r.stderr.strip()[-200:]}")
        else:
            rep.restored += 1


def declared_reset(scenario: dict | Path) -> str:
    """The scenario's reset level, 'api' or 'vm' (default 'vm').

    Reads the optional top-level `reset` key of scenario.yaml: either the string, or a mapping
    with a `mode`/`level` entry (the existing `reset: {strategy, ...}` mapping means 'vm').
    """
    if not isinstance(scenario, dict):
        p = Path(scenario)
        p = p / "scenario.yaml" if p.is_dir() else p
        scenario = yaml.safe_load(re.sub(r"\{\{\s*\w+\s*\}\}", "X", p.read_text())) or {}
    val = scenario.get("reset")
    if isinstance(val, dict):
        val = val.get("mode") or val.get("level")
    return val if val in ("api", "vm") else "vm"
