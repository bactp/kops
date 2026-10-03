# Must FAIL: an initialDelaySeconds of 10 is still shorter than the start-up time, so restarts continue.
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","livenessProbe":{"initialDelaySeconds":10}}]}}}}'
