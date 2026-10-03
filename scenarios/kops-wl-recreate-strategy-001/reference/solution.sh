# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get deployment {{app}} -o jsonpath={.spec.strategy}
kubectl -n {{ns}} patch deployment {{app}} --type merge -p '{"spec":{"strategy":{"type":"Recreate","rollingUpdate":null}}}'
kubectl -n {{ns}} set env deployment/{{app}} MSG={{ver}}
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
