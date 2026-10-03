# Must FAIL: the ServiceAccount is attached but the token is still mounted.
kubectl -n {{ns}} create serviceaccount {{sa}}
kubectl -n {{ns}} set serviceaccount deployment/{{app}} {{sa}}
