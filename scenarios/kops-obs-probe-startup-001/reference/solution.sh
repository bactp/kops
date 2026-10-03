# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} describe pods
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","startupProbe":{"httpGet":{"path":"/healthz","port":{{port}}},"periodSeconds":5,"failureThreshold":12}}]}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=150s
