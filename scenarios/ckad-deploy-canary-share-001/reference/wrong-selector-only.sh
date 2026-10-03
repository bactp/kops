# Must FAIL: the selector is opened but the canary has no pods and stable still runs 4 replicas.
kubectl -n {{ns}} patch service {{app}} --type json -p '[{"op":"remove","path":"/spec/selector/track"}]'
