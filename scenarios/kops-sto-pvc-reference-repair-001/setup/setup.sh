#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl apply -f "$KOPS_FIXTURES/pvcs.yaml"
kubectl apply -f "$KOPS_FIXTURES/writer.yaml"
kubectl -n "$KOPS_P_NS" wait --for=condition=Ready pod/writer --timeout=120s
sleep 3
kubectl -n "$KOPS_P_NS" exec writer -- cat /data/state.txt
kubectl -n "$KOPS_P_NS" delete pod writer --now
kubectl -n "$KOPS_P_NS" wait --for=jsonpath='{.status.phase}'=Bound "pvc/$KOPS_P_APP-data" --timeout=60s
kubectl apply -f "$KOPS_FIXTURES/service.yaml"
kubectl apply -f "$KOPS_FIXTURES/deployment.yaml"
sleep 5
