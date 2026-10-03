#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/app.yaml"
for i in $(seq 1 40); do
  kubectl -n "$KOPS_P_NS" get pods -o jsonpath='{.items[*].status.containerStatuses[*].restartCount}' | grep -q '[1-9]' && break
  sleep 3
done
