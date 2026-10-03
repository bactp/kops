#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
kubectl -n "$KOPS_P_NS" create serviceaccount "$KOPS_P_SA"
kubectl -n "$KOPS_P_NS" create role "$KOPS_P_APP-deployer" --verb=get,list,patch --resource=deployments
kubectl -n "$KOPS_P_NS" patch role "$KOPS_P_APP-deployer" --type json -p '[{"op":"add","path":"/rules/-","value":{"apiGroups":[""],"resources":["deployments/scale"],"verbs":["update"]}}]'
kubectl -n "$KOPS_P_NS" create rolebinding "$KOPS_P_APP-deployer" --role="$KOPS_P_APP-deployer" --serviceaccount="default:$KOPS_P_SA"
