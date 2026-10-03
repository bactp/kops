#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
 kubectl create namespace "$KOPS_P_NS"
 kubectl apply -f "$KOPS_FIXTURES/web.yaml"
 kubectl apply -f "$KOPS_FIXTURES/service.yaml"
 kubectl apply -f "$KOPS_FIXTURES/clients.yaml"
 kubectl -n "$KOPS_P_NS" rollout status deployment/$KOPS_P_APP --timeout=120s
kubectl -n "$KOPS_P_NS" rollout status deployment/client --timeout=120s
kubectl -n "$KOPS_P_NS" rollout status deployment/scanner --timeout=120s
 kubectl apply -f "$KOPS_FIXTURES/policies.yaml"
 sleep 8
