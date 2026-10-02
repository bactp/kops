# Must FAIL: selector fixed but targetPort still wrong.
kubectl -n {{ns}} patch service {{app}} --type merge -p '{"spec":{"selector":{"app":"{{app}}","tier":"web"}}}'
