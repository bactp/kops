#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/configmap.yaml"
kubectl apply -f "$KOPS_FIXTURES/svc.yaml"
kubectl apply -f "$KOPS_FIXTURES/web.yaml"
sleep 5
