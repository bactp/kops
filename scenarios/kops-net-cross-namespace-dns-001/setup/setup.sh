#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl create namespace "$KOPS_P_NS-backend"
kubectl apply -f "$KOPS_FIXTURES/backend.yaml"
kubectl apply -f "$KOPS_FIXTURES/client.yaml"
kubectl -n "$KOPS_P_NS-backend" rollout status deployment/"$KOPS_P_SVC" --timeout=120s
kubectl -n "$KOPS_P_NS" rollout status deployment/client --timeout=120s
sleep 8
