#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/releases.yaml"
kubectl apply -f "$KOPS_FIXTURES/service.yaml"
kubectl -n "$KOPS_P_NS" rollout status deployment/"$KOPS_P_APP-stable" --timeout=120s
