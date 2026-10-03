#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
NODES=($(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[*].metadata.name}'))
kubectl label node "${NODES[0]}" hold=cordon
kubectl label node "${NODES[1]}" hold=taint
kubectl cordon "${NODES[0]}"
kubectl taint node "${NODES[1]}" "$KOPS_P_KEY=true:NoSchedule"
kubectl apply -f "$KOPS_FIXTURES/web.yaml"
sleep 5
