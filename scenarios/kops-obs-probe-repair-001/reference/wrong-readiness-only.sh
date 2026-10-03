# Must FAIL: the readiness probe is fixed but the liveness probe still kills the container.
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","readinessProbe":{"httpGet":{"path":"/healthz","port":{{port}}}}}]}}}}'
