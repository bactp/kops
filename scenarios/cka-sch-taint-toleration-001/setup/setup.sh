#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
NODE=$(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[0].metadata.name}')
kubectl label node "$NODE" "dedicated=$KOPS_P_TEAM"
kubectl taint node "$NODE" "dedicated=$KOPS_P_TEAM:NoSchedule"
kubectl apply -f "$KOPS_FIXTURES/web.yaml"
sleep 5
