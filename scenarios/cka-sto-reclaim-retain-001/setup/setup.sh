#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/volumes.yaml"
kubectl -n "$KOPS_P_NS" wait --for=jsonpath='{.status.phase}'=Bound "pvc/$KOPS_P_APP-data" --timeout=60s
kubectl -n "$KOPS_P_NS" wait --for=jsonpath='{.status.phase}'=Bound "pvc/$KOPS_P_APP-cache" --timeout=60s
