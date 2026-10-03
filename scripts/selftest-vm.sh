#!/usr/bin/env bash
# Validate scenarios on the KubeVirt provider with N parallel shards, then update catalog/available.txt and
# catalog/reset-api.txt from the results.
#   KUBECONFIG=~/kops-k8s.kubeconfig SHARDS=2 WORKERS=0 scripts/selftest-vm.sh
# Re-run `scripts/deploy.sh` afterwards to publish the new lists (they live in a ConfigMap, no image rebuild needed).
set -euo pipefail
cd "$(dirname "$0")/.."
SHARDS="${SHARDS:-2}"; WORKERS="${WORKERS:-0}"; RUN="${RUN:-$(date +%H%M%S)}"
VERSION="${VERSION:-$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)}"
IMAGE="${IMAGE:-localhost/kops/platform:${VERSION}}"
OUT=deploy/out; mkdir -p "$OUT"
for i in $(seq 1 "$SHARDS"); do
  name="selftest-vm-w${WORKERS}-${RUN}-${i}"
  sed -e "s#__NAME__#${name}#" -e "s#__IMAGE__#${IMAGE}#" -e "s#__WORKERS__#${WORKERS}#" -e "s#__SHARD__#${i}/${SHARDS}#" \
    deploy/k8s/40-selftest-job.yaml | kubectl apply -f -
  echo "$name" >> "$OUT/selftest-${RUN}.jobs"
done
echo "started: $(tr '\n' ' ' < "$OUT/selftest-${RUN}.jobs")"
echo "wait:    kubectl -n kops-gw wait --for=condition=complete --timeout=8h job -l app=kops-selftest"
echo "collect: RUN=${RUN} scripts/collect-selftest-vm.sh"
