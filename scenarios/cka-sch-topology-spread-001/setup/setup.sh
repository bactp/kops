#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
NODES=($(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[*].metadata.name}'))
kubectl label node "${NODES[0]}" rack=r1
kubectl label node "${NODES[1]}" rack=r2
kubectl apply -f "$KOPS_FIXTURES/web.yaml"
kubectl -n "$KOPS_P_NS" rollout status deployment/"$KOPS_P_APP" --timeout=120s
