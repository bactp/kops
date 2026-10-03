#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
kubectl create namespace "$KOPS_P_NS"
mk() { # name memory failing
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata: {name: $1, namespace: $KOPS_P_NS}
spec:
  restartPolicy: Never
  containers:
    - name: c
      image: busybox:1.36.1
      imagePullPolicy: IfNotPresent
      command: ["sh", "-c", "$3"]
      resources: {requests: {memory: $2}}
EOF
}
first_fail=$((6 - KOPS_P_NFAIL))
for i in 1 2 3 4 5; do
  mem=64Mi; [ "$i" -eq "$KOPS_P_BIGIDX" ] && mem=512Mi
  cmd="sleep 3600"; [ "$i" -ge "$first_fail" ] && cmd="exit 1"
  mk "$KOPS_P_PRE-$i" "$mem" "$cmd"
  sleep 2
done
sleep 5
