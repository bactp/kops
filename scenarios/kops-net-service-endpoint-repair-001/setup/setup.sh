#!/usr/bin/env bash
# Injects the fault. Runs as verifier-admin on the runner. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/deployment.yaml"
kubectl -n "$KOPS_P_NS" rollout status "deployment/$KOPS_P_APP" --timeout=120s
kubectl apply -f "$KOPS_FIXTURES/service-broken.yaml"
