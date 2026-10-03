#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl -n "$KOPS_P_NS" create serviceaccount "$KOPS_P_SA"
kubectl -n "$KOPS_P_NS" create configmap sample --from-literal=k=v
kubectl -n "$KOPS_P_NS" create secret generic sample --from-literal=k=v
kubectl -n "$KOPS_P_NS" run sample-pod --image=busybox:1.36.1 --image-pull-policy=IfNotPresent -- sleep 3600
