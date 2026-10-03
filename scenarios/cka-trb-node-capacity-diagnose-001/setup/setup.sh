#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
NODES=($(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[*].metadata.name}'))
kubectl label node "${NODES[0]}" pool=a
kubectl label node "${NODES[1]}" pool=b
kubectl label node "${NODES[2]}" pool=c
pools=(a b c)
others=()
for p in "${pools[@]}"; do [ "$p" != "$KOPS_P_HEAVY" ] && others+=("$p"); done
mk() { # name pool replicas cpu
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata: {name: $1, namespace: $KOPS_P_NS}
spec:
  replicas: $3
  selector: {matchLabels: {app: $1}}
  template:
    metadata: {labels: {app: $1}}
    spec:
      nodeSelector: {pool: "$2"}
      containers:
        - name: c
          image: busybox:1.36.1
          imagePullPolicy: IfNotPresent
          command: ["sleep", "3600"]
          resources: {requests: {cpu: $4}}
EOF
}
mk big "$KOPS_P_HEAVY" 1 700m
mk many "${others[0]}" 3 200m
mk some "${others[1]}" 2 250m
for d in big many some; do kubectl -n "$KOPS_P_NS" rollout status deployment/$d --timeout=120s; done
