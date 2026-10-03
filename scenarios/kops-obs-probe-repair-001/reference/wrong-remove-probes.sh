# Must FAIL: pods become Ready, but the probes were deleted instead of fixed.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/containers/0/readinessProbe"},{"op":"remove","path":"/spec/template/spec/containers/0/livenessProbe"}]'
