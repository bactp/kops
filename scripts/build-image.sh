#!/usr/bin/env bash
# Build the platform image with docker on this machine and import it into containerd on every worker (no registry yet).
#   KEY=~/workflow-prj.pem WORKERS="192.168.28.139 192.168.28.200" scripts/build-image.sh
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="${VERSION:-$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)}"
IMAGE="${IMAGE:-localhost/kops/platform:${VERSION}}"
KEY="${KEY:-$HOME/workflow-prj.pem}"; WORKERS="${WORKERS:?set WORKERS to the worker node IPs}"
docker build -t "$IMAGE" .
for h in $WORKERS; do
  echo "== importing $IMAGE into $h"
  docker save "$IMAGE" | ssh -i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "ubuntu@$h" 'sudo ctr -n k8s.io images import -' | tail -1
done
echo "$IMAGE"
