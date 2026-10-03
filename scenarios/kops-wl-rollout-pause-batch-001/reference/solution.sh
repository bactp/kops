# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} rollout pause deployment/{{app}}
kubectl -n {{ns}} set env deployment/{{app}} MSG={{msg}}
kubectl -n {{ns}} set resources deployment/{{app}} --limits=cpu={{cpu}}
kubectl -n {{ns}} set serviceaccount deployment/{{app}} {{sa}}
kubectl -n {{ns}} rollout resume deployment/{{app}}
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
