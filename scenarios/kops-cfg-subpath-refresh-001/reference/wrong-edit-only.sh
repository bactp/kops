# Must FAIL: the ConfigMap is edited but the subPath-mounted file in running pods is never refreshed.
kubectl -n {{ns}} patch configmap {{app}}-page --type merge -p '{"data":{"index.html":"{{new}}"}}'
