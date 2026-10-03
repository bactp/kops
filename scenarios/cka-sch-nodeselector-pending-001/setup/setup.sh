#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
NODES=($(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[*].metadata.name}'))
kubectl label node "${NODES[0]}" pool=general
kubectl label node "${NODES[1]}" "pool=$KOPS_P_POOL"
kubectl apply -f "$KOPS_FIXTURES/web.yaml"
sleep 5
