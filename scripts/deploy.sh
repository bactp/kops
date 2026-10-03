#!/usr/bin/env bash
# Install or upgrade the platform (API + dashboard + bundled Keycloak) on the host cluster.
#   KUBECONFIG=~/kops-k8s.kubeconfig NODE_IP=192.168.28.124 ADMIN_USERS=alice scripts/deploy.sh
# Prerequisites: the cluster has KubeVirt, CDI and Longhorn; the golden image and the platform image are imported on the
# workers (scripts/golden/*, scripts/build-image.sh).
set -euo pipefail
cd "$(dirname "$0")/.."
: "${NODE_IP:?set NODE_IP to a node address reachable by your browsers}"
VERSION="${VERSION:-$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)}"
export PUBLIC_URL="${PUBLIC_URL:-http://$NODE_IP:30800}" AUTH_URL="${AUTH_URL:-http://$NODE_IP:30880}"
export IMAGE="${IMAGE:-localhost/kops/platform:${VERSION}}" GOLDEN_IMAGE="${GOLDEN_IMAGE:-localhost/kops/node-golden:v3}"
export KEYCLOAK_IMAGE="${KEYCLOAK_IMAGE:-quay.io/keycloak/keycloak:26.8.0}" ADMIN_USERS="${ADMIN_USERS:-}" MAX_SESSIONS="${MAX_SESSIONS:-}"
OUT=deploy/out; mkdir -p "$OUT"
python3 - <<'PY'
import os, pathlib
e = os.environ
realm = pathlib.Path("deploy/kops-realm.json").read_text().replace("__PUBLIC_URL__", e["PUBLIC_URL"])
for name in ("20-platform.yaml", "30-keycloak.yaml"):
    t = pathlib.Path("deploy/k8s", name).read_text()
    t = t.replace("__REALM_JSON__", "\n".join("    " + l for l in realm.splitlines()))
    for k, v in {"__PUBLIC_URL__": e["PUBLIC_URL"], "__AUTH_URL__": e["AUTH_URL"], "__IMAGE__": e["IMAGE"],
                 "__GOLDEN_IMAGE__": e["GOLDEN_IMAGE"], "__KEYCLOAK_IMAGE__": e["KEYCLOAK_IMAGE"],
                 "__ADMIN_USERS__": e["ADMIN_USERS"], "__MAX_SESSIONS__": e["MAX_SESSIONS"]}.items():
        t = t.replace(k, v)
    if not e["MAX_SESSIONS"]:
        t = "\n".join(l for l in t.splitlines() if "KOPS_MAX_SESSIONS" not in l)
    pathlib.Path("deploy/out", name).write_text(t)
PY
kubectl apply -f deploy/k8s/00-namespaces.yaml -f deploy/k8s/10-rbac.yaml
mkdir -p "$HOME/.kops-secrets"; chmod 700 "$HOME/.kops-secrets"
if ! kubectl -n kops-gw get secret kops-platform-secret >/dev/null 2>&1; then
  kubectl -n kops-gw create secret generic kops-platform-secret --from-literal=KOPS_SESSION_SECRET="$(openssl rand -hex 32)" >/dev/null
fi
if ! kubectl -n kops-auth get secret keycloak-admin >/dev/null 2>&1; then
  pw="$(openssl rand -base64 18 | tr -d '/+=')"
  kubectl -n kops-auth create secret generic keycloak-admin --from-literal=password="$pw" >/dev/null
  printf '%s\n' "$pw" > "$HOME/.kops-secrets/keycloak-admin.password"; chmod 600 "$HOME/.kops-secrets/keycloak-admin.password"
  echo "Keycloak admin user 'kcadmin'; password saved to ~/.kops-secrets/keycloak-admin.password"
fi
kubectl apply -f "$OUT/30-keycloak.yaml"
kubectl -n kops-auth rollout status deploy/keycloak --timeout=600s
kubectl -n kops-gw create configmap kops-catalog --from-file=available.txt=catalog/available.txt --from-file=reset-api.txt=catalog/reset-api.txt --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "$OUT/20-platform.yaml"
kubectl -n kops-gw rollout restart deploy/kops-platform >/dev/null   # the catalogue is read at start
kubectl -n kops-gw rollout status deploy/kops-platform --timeout=300s
echo "Dashboard: $PUBLIC_URL   Identity provider: $AUTH_URL   (register an account, then it is an admin if its username is in ADMIN_USERS)"
