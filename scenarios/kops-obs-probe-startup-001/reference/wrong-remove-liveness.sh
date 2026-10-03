# Must FAIL: without a liveness probe nothing restarts, but a hung app would never be recovered.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/containers/0/livenessProbe"}]'
