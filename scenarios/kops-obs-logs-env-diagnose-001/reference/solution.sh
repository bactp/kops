# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods
kubectl -n {{ns}} logs deployment/{{app}}
kubectl -n {{ns}} get services
kubectl -n {{ns}} set env deployment/{{app}} CACHE_HOST={{cache}}
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
