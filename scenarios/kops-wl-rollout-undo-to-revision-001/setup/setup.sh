#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/deployment.yaml"
kubectl -n "$KOPS_P_NS" rollout status "deployment/$KOPS_P_APP" --timeout=120s
kubectl apply -f "$KOPS_FIXTURES/service.yaml"
kubectl -n "$KOPS_P_NS" set env "deployment/$KOPS_P_APP" MSG="${KOPS_P_COLOR}-2"
kubectl -n "$KOPS_P_NS" rollout status "deployment/$KOPS_P_APP" --timeout=120s
kubectl -n "$KOPS_P_NS" set image "deployment/$KOPS_P_APP" web=busybox:1.36.99
