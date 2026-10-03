#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl label namespace "$KOPS_P_NS" pod-security.kubernetes.io/enforce=restricted pod-security.kubernetes.io/enforce-version=latest
kubectl apply -f "$KOPS_FIXTURES/service.yaml"
kubectl apply -f "$KOPS_FIXTURES/deployment.yaml" 2>/dev/null
sleep 5
