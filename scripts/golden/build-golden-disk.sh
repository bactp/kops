#!/usr/bin/env bash
# Runs ON A CLUSTER NODE (it needs to reach VM pod IPs). Builds the golden node disk as a PVC in namespace `golden`.
#   VERSION=v3 BASE_PVC=ubuntu-base scripts/golden/build-golden-disk.sh
# BASE_PVC defaults to `ubuntu-base`, an Ubuntu 22.04 cloud image imported by this script when missing.
# Set BASE_PVC=node-golden-v2 (any earlier golden PVC) to build on top of it, which is much faster.
set -euo pipefail
VERSION="${VERSION:-v3}"; BASE_PVC="${BASE_PVC:-ubuntu-base}"; SC="${SC:-longhorn-1r}"; NS=golden
OUT_PVC="node-golden-${VERSION}"; HERE="$(cd "$(dirname "$0")" && pwd)"
KEY="$HOME/.ssh/nested_id"; [ -f "$KEY" ] || ssh-keygen -q -t ed25519 -N '' -f "$KEY"
SSHO="-i $KEY -o BatchMode=yes -o ConnectTimeout=4 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
log() { echo "[$(date +%H:%M:%S)] $*"; }
kubectl get ns $NS >/dev/null 2>&1 || kubectl create ns $NS >/dev/null
if ! kubectl -n $NS get pvc "$BASE_PVC" >/dev/null 2>&1; then
  [ "$BASE_PVC" = ubuntu-base ] || { echo "base PVC $BASE_PVC not found" >&2; exit 1; }
  log "importing the Ubuntu 22.04 cloud image (one time, several minutes)"
  kubectl -n $NS apply -f - >/dev/null <<YAML
apiVersion: cdi.kubevirt.io/v1beta1
kind: DataVolume
metadata: {name: ubuntu-base}
spec:
  source: {http: {url: "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"}}
  storage: {resources: {requests: {storage: 10Gi}}, storageClassName: $SC}
YAML
  for i in $(seq 1 300); do [ "$(kubectl -n $NS get dv ubuntu-base -o jsonpath='{.status.phase}')" = Succeeded ] && break; sleep 5; done
fi
kubectl -n $NS delete vm "builder-$VERSION" --ignore-not-found --wait=true >/dev/null 2>&1
kubectl -n $NS delete dv "$OUT_PVC" --ignore-not-found --wait=true >/dev/null 2>&1
log "cloning $BASE_PVC -> $OUT_PVC"
kubectl -n $NS apply -f - >/dev/null <<YAML
apiVersion: cdi.kubevirt.io/v1beta1
kind: DataVolume
metadata: {name: $OUT_PVC}
spec:
  source: {pvc: {name: $BASE_PVC, namespace: $NS}}
  storage: {resources: {requests: {storage: 10Gi}}, storageClassName: $SC}
YAML
for i in $(seq 1 120); do [ "$(kubectl -n $NS get dv $OUT_PVC -o jsonpath='{.status.phase}')" = Succeeded ] && break; sleep 2; done
PUB=$(cat "$KEY.pub")
kubectl -n $NS apply -f - >/dev/null <<YAML
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata: {name: builder-$VERSION}
spec:
  runStrategy: Always
  template:
    spec:
      domain:
        cpu: {cores: 2}
        resources: {requests: {memory: 3Gi}}
        devices:
          disks: [{name: root, disk: {bus: virtio}}, {name: ci, disk: {bus: virtio}}]
      volumes:
        - name: root
          persistentVolumeClaim: {claimName: $OUT_PVC}
        - name: ci
          cloudInitNoCloud:
            userData: |
              #cloud-config
              hostname: node
              users:
                - {name: ubuntu, sudo: "ALL=(ALL) NOPASSWD:ALL", shell: /bin/bash, ssh_authorized_keys: ["$PUB"]}
YAML
for i in $(seq 1 300); do ip=$(kubectl -n $NS get vmi "builder-$VERSION" -o jsonpath='{.status.interfaces[0].ipAddress}' 2>/dev/null); [ -n "$ip" ] && ssh $SSHO ubuntu@$ip true 2>/dev/null && break; sleep 2; done
log "builder up ($ip); provisioning"
ssh $SSHO ubuntu@$ip 'bash -s' < "$HERE/provision-node.sh"
log "graceful shutdown"
kubectl -n $NS patch vm "builder-$VERSION" --type merge -p '{"spec":{"runStrategy":"Halted"}}' >/dev/null
for i in $(seq 1 180); do kubectl -n $NS get vmi "builder-$VERSION" >/dev/null 2>&1 || break; sleep 1; done
kubectl -n $NS delete vm "builder-$VERSION" --wait=true >/dev/null 2>&1
log "golden disk ready: pvc/$OUT_PVC in namespace $NS"
