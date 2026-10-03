# Must FAIL: the changes are batched but the rollout is never resumed.
kubectl -n {{ns}} rollout pause deployment/{{app}}
kubectl -n {{ns}} set env deployment/{{app}} MSG={{msg}}
kubectl -n {{ns}} set resources deployment/{{app}} --limits=cpu={{cpu}}
kubectl -n {{ns}} set serviceaccount deployment/{{app}} {{sa}}
