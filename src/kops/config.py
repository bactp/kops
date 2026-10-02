"""Pinned versions and paths. Nothing here reads the user's kubeconfig."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = Path(os.environ.get("KOPS_BIN", Path.home() / ".local/share/kops/bin"))
KIND = BIN_DIR / "kind"
KUBECTL = BIN_DIR / "kubectl"

RUN_DIR = ROOT / ".kops-run"      # kubeconfigs, scratch; git-ignored
RESULTS_DIR = ROOT / "results"    # git-ignored
SCENARIOS_DIR = ROOT / "scenarios"

KUBERNETES_VERSION = "1.35"
KIND_NODE_IMAGE = (
    "kindest/node:v1.35.8@sha256:"
    "07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0"
)
# Images preloaded into every cluster so trials do not depend on the internet.
PROFILE_IMAGES = [
    "busybox:1.36.1",
    "registry.k8s.io/e2e-test-images/agnhost:2.53",
]
PROBE_NAMESPACE = "kops-probe"
PROBE_POD = "probe"
PROBE_IMAGE = "busybox:1.36.1"
CLUSTER_PREFIX = "kops-"
