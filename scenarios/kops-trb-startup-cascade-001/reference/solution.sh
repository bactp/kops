# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods
kubectl -n {{ns}} describe replicaset
kubectl -n {{ns}} create serviceaccount {{sa}}
kubectl -n {{ns}} get pods
kubectl -n {{ns}} describe pods
kubectl -n {{ns}} get configmap
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"volumes":[{"name":"site","configMap":{"name":"{{app}}-conf"}}]}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
kubectl -n {{ns}} get endpoints {{app}}
kubectl -n {{ns}} patch service {{app}} --type json -p '[{"op":"replace","path":"/spec/ports/0/targetPort","value":{{port}}}]'
