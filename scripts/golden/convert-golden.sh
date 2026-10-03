#!/usr/bin/env bash
# Runs ON A CLUSTER NODE. Converts the golden PVC to a compressed qcow2 on the hostPath of `kops-worker-1`:
#   /var/tmp/kops-golden/node-golden-<VERSION>.qcow2     then use publish-golden.sh from a workstation.
set -euo pipefail
VERSION="${VERSION:-v3}"; NODE="${NODE:-kops-worker-1}"; NS=golden; PVC="node-golden-${VERSION}"
kubectl -n $NS delete pod convert --ignore-not-found --wait=true >/dev/null 2>&1
kubectl -n $NS apply -f - >/dev/null <<YAML
apiVersion: v1
kind: Pod
metadata: {name: convert}
spec:
  restartPolicy: Never
  nodeSelector: {kubernetes.io/hostname: $NODE}
  containers:
    - name: c
      image: quay.io/kubevirt/cdi-importer:v1.66.1
      securityContext: {runAsUser: 0}
      command: ["sh","-c","qemu-img convert -O qcow2 -c -m 8 -W /pvc/disk.img /out/node-golden-${VERSION}.qcow2 && ls -la /out"]
      volumeMounts: [{name: pvc, mountPath: /pvc, readOnly: true}, {name: out, mountPath: /out}]
  volumes:
    - name: pvc
      persistentVolumeClaim: {claimName: $PVC, readOnly: true}
    - name: out
      hostPath: {path: /var/tmp/kops-golden, type: DirectoryOrCreate}
YAML
for i in $(seq 1 360); do ph=$(kubectl -n $NS get pod convert -o jsonpath='{.status.phase}'); [ "$ph" = Succeeded ] || [ "$ph" = Failed ] && break; sleep 5; done
kubectl -n $NS logs convert | tail -3; kubectl -n $NS delete pod convert --wait=false >/dev/null 2>&1
[ "$ph" = Succeeded ]
