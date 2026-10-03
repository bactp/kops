#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/configmap.yaml"
kubectl apply -f "$KOPS_FIXTURES/service.yaml"
kubectl apply -f "$KOPS_FIXTURES/deployment.yaml"
for i in $(seq 1 30); do
  kubectl -n "$KOPS_P_NS" get pods -o jsonpath='{.items[*].status.containerStatuses[*].state.waiting.reason}' | grep -q CreateContainerConfigError && break
  sleep 2
done
