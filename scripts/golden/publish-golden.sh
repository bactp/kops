#!/usr/bin/env bash
# Runs on a WORKSTATION with ssh access to the worker nodes. Wraps the qcow2 as an OCI image and imports it into
# containerd on every worker (no registry needed).
#   KEY=~/workflow-prj.pem WORKERS="192.168.28.139 192.168.28.200" VERSION=v3 scripts/golden/publish-golden.sh
set -euo pipefail
VERSION="${VERSION:-v3}"; KEY="${KEY:-$HOME/workflow-prj.pem}"; WORKERS="${WORKERS:?set WORKERS}"
SRC_HOST="${SRC_HOST:-${WORKERS%% *}}"; REF="localhost/kops/node-golden:${VERSION}"
HERE="$(cd "$(dirname "$0")" && pwd)"; TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
SSH="ssh -i $KEY -o BatchMode=yes -o StrictHostKeyChecking=accept-new"; SCP="scp -q -i $KEY -o BatchMode=yes"
$SCP "ubuntu@$SRC_HOST:/var/tmp/kops-golden/node-golden-${VERSION}.qcow2" "$TMP/node-golden-${VERSION}.qcow2"
python3 "$HERE/oci_from_qcow2.py" "$TMP/node-golden-${VERSION}.qcow2" "$TMP/node-golden.oci.tar" "$REF"
for h in $WORKERS; do
  echo "== $h"
  $SCP "$TMP/node-golden.oci.tar" "ubuntu@$h:/tmp/node-golden.oci.tar"
  $SSH "ubuntu@$h" "sudo ctr -n k8s.io images import --index-name $REF /tmp/node-golden.oci.tar >/dev/null && rm -f /tmp/node-golden.oci.tar && sudo ctr -n k8s.io images ls -q | grep -F node-golden"
done
$SSH "ubuntu@$SRC_HOST" 'sudo rm -rf /var/tmp/kops-golden'
