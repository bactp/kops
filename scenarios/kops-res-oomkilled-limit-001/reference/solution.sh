# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods
kubectl -n {{ns}} describe pods
kubectl -n {{ns}} set resources deployment/{{app}} --requests=memory=64Mi --limits=memory=160Mi
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
