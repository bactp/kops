#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl -n kube-system rollout status daemonset/kube-proxy --timeout=120s
kubectl -n kube-system set image daemonset/kube-proxy kube-proxy=registry.k8s.io/kube-proxy:v1.35.99-broken
for i in $(seq 1 40); do
  n=$(kubectl -n kube-system get pods -l k8s-app=kube-proxy --field-selector=status.phase=Running -o name | wc -l)
  [ "$n" -eq 0 ] && break
  sleep 2
done
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/web.yaml"
kubectl apply -f "$KOPS_FIXTURES/service.yaml"
kubectl -n "$KOPS_P_NS" rollout status deployment/"$KOPS_P_APP" --timeout=120s
sleep 5
