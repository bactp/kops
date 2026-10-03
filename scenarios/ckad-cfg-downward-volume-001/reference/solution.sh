# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get deployment {{app}} -o yaml
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"replace","path":"/spec/template/spec/volumes/0","value":{"name":"podinfo","downwardAPI":{"items":[{"path":"labels","fieldRef":{"fieldPath":"metadata.labels"}},{"path":"namespace","fieldRef":{"fieldPath":"metadata.namespace"}}]}}}]'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
