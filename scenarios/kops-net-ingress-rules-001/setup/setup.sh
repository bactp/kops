#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
 kubectl create namespace "$KOPS_P_NS"
 kubectl apply -f "$KOPS_FIXTURES/backends.yaml"
 kubectl apply -f "$KOPS_FIXTURES/ingressclass.yaml"
 kubectl -n "$KOPS_P_NS" rollout status deployment/$KOPS_P_APP-api --timeout=120s
kubectl -n "$KOPS_P_NS" rollout status deployment/$KOPS_P_APP-web --timeout=120s
