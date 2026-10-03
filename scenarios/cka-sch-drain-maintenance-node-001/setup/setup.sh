#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
NODES=($(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[*].metadata.name}'))
kubectl label node "${NODES[1]}" maintenance=scheduled
kubectl apply -f "$KOPS_FIXTURES/web.yaml"
kubectl -n "$KOPS_P_NS" rollout status deployment/"$KOPS_P_APP" --timeout=120s
for i in $(seq 1 20); do
  n=$(kubectl -n "$KOPS_P_NS" get pods -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' | grep -c "${NODES[1]}" || true)
  [ "$n" -ge 1 ] && break
  sleep 2
done
