# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} rollout history deployment/{{app}}
kubectl -n {{ns}} rollout history deployment/{{app}} --revision=1
kubectl -n {{ns}} rollout undo deployment/{{app}} --to-revision=1
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
