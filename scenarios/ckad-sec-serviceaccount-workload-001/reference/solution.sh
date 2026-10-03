# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} create serviceaccount {{sa}}
kubectl -n {{ns}} set serviceaccount deployment/{{app}} {{sa}}
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"automountServiceAccountToken":false}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
