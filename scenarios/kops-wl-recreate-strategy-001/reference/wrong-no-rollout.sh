# Must FAIL: strategy is correct but the new release was never rolled out.
kubectl -n {{ns}} patch deployment {{app}} --type merge -p '{"spec":{"strategy":{"type":"Recreate","rollingUpdate":null}}}'
