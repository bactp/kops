# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} describe pods
kubectl -n {{ns}} get endpoints {{app}}
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","readinessProbe":{"httpGet":{"path":"/healthz","port":{{port}}}},"livenessProbe":{"tcpSocket":{"port":{{port}}}}}]}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
