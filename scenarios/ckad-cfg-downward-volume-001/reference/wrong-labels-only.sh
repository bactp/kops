# Must FAIL: the namespace file is missing.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"replace","path":"/spec/template/spec/volumes/0","value":{"name":"podinfo","downwardAPI":{"items":[{"path":"labels","fieldRef":{"fieldPath":"metadata.labels"}}]}}}]'
