# Must FAIL: setting only strategy.type is rejected by the API because the rollingUpdate block remains, so nothing changes.
kubectl -n {{ns}} patch deployment {{app}} --type merge -p '{"spec":{"strategy":{"type":"Recreate"}}}'
kubectl -n {{ns}} set env deployment/{{app}} MSG={{ver}}
