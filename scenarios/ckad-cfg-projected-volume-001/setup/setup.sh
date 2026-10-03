#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl -n "$KOPS_P_NS" create configmap "$KOPS_P_APP-page" --from-literal=index.html="page-ok"
kubectl -n "$KOPS_P_NS" create secret generic "$KOPS_P_APP-token" --from-literal=token="$KOPS_P_TOK"
kubectl apply -f "$KOPS_FIXTURES/service.yaml"
kubectl apply -f "$KOPS_FIXTURES/deployment.yaml"
kubectl -n "$KOPS_P_NS" rollout status deployment/"$KOPS_P_APP" --timeout=120s
