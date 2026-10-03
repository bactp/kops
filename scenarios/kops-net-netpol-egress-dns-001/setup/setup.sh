#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
 kubectl create namespace "$KOPS_P_NS"
 kubectl apply -f "$KOPS_FIXTURES/apps.yaml"
 kubectl apply -f "$KOPS_FIXTURES/client.yaml"
 kubectl -n "$KOPS_P_NS" rollout status deployment/$KOPS_P_APP --timeout=120s
kubectl -n "$KOPS_P_NS" rollout status deployment/$KOPS_P_OTHER --timeout=120s
kubectl -n "$KOPS_P_NS" rollout status deployment/client --timeout=120s
 kubectl apply -f "$KOPS_FIXTURES/policy.yaml"
 sleep 8
