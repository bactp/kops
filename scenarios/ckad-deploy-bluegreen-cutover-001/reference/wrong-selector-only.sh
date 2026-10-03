# Must FAIL: the Service is switched while green has no pods, so there are no endpoints.
kubectl -n {{ns}} patch service {{app}} -p '{"spec":{"selector":{"app":"{{app}}","track":"green"}}}'
