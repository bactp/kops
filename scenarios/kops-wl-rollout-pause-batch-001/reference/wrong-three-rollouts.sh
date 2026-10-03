# Must FAIL: the changes are applied one by one, producing three new revisions.
kubectl -n {{ns}} set env deployment/{{app}} MSG={{msg}}
kubectl -n {{ns}} set resources deployment/{{app}} --limits=cpu={{cpu}}
kubectl -n {{ns}} set serviceaccount deployment/{{app}} {{sa}}
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
