# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get deployments,service -o wide
kubectl -n {{ns}} scale deployment/{{app}}-green --replicas=3
kubectl -n {{ns}} rollout status deployment/{{app}}-green --timeout=120s
kubectl -n {{ns}} patch service {{app}} -p '{"spec":{"selector":{"app":"{{app}}","track":"green"}}}'
