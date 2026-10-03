#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/backend.yaml"
kubectl apply -f "$KOPS_FIXTURES/app.yaml"
kubectl -n "$KOPS_P_NS" rollout status deployment/"$KOPS_P_DEP-server" --timeout=120s
sleep 8
