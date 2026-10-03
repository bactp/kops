# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} create secret generic {{app}}-db --from-literal=username={{user}} --from-literal=password={{pw}}
kubectl -n {{ns}} set env deployment/{{app}} --from=secret/{{app}}-db --prefix=DB_
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
