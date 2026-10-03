#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl -n kube-system rollout status deployment/coredns --timeout=120s
CF="$(mktemp)"
kubectl -n kube-system get configmap coredns -o jsonpath='{.data.Corefile}' | sed 's/kubernetes cluster\.local/kubernetes cluster.lcl/' > "$CF"
grep -q 'cluster.lcl' "$CF"
kubectl -n kube-system create configmap coredns --from-file=Corefile="$CF" --dry-run=client -o yaml | kubectl apply -f -
rm -f "$CF"
kubectl -n kube-system rollout restart deployment/coredns
kubectl -n kube-system rollout status deployment/coredns --timeout=120s
for i in $(seq 1 20); do
  kubectl -n kops-probe exec probe -- nslookup kubernetes.default.svc.cluster.local >/dev/null 2>&1 || break
  sleep 2
done
kubectl -n kube-system patch service kube-dns --type merge -p '{"spec":{"selector":{"k8s-app":"kube-dns-legacy"}}}'
kubectl create namespace "$KOPS_P_NS"
for i in $(seq 1 30); do
  kubectl -n kops-probe exec probe -- nslookup kubernetes.default.svc.cluster.local >/dev/null 2>&1 || break
  sleep 2
done
