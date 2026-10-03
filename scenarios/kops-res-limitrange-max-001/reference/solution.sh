# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} describe replicaset
kubectl -n {{ns}} get limitrange {{app}}-limits -o yaml
kubectl -n {{ns}} set resources deployment/{{app}} --requests=memory=100Mi --limits=memory=200Mi
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
