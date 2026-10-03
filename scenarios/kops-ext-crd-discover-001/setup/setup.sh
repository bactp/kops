#!/usr/bin/env bash
# Injects the fault as verifier-admin. Inputs: KUBECONFIG, KOPS_P_*, KOPS_FIXTURES.
set -euo pipefail
PLURAL="$(echo "$KOPS_P_KIND" | tr 'A-Z' 'a-z')s"
GROUP="$KOPS_P_GRP.kops.example"
kubectl create namespace "$KOPS_P_NS"
cat <<EOF | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: $PLURAL.$GROUP
spec:
  group: $GROUP
  scope: Namespaced
  names:
    kind: $KOPS_P_KIND
    plural: $PLURAL
    singular: $(echo "$KOPS_P_KIND" | tr 'A-Z' 'a-z')
    shortNames: [$KOPS_P_SHORT]
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                phase: {type: string}
                size: {type: integer}
EOF
kubectl wait --for=condition=Established "crd/$PLURAL.$GROUP" --timeout=60s
for i in 1 2 3 4; do
  if [ "$i" -le "$KOPS_P_NREADY" ]; then phase=Ready; else phase=Pending; fi
  cat <<EOF | kubectl apply -f -
apiVersion: $GROUP/v1
kind: $KOPS_P_KIND
metadata: {name: item-$i, namespace: $KOPS_P_NS}
spec: {phase: $phase, size: $((i * 10))}
EOF
done
