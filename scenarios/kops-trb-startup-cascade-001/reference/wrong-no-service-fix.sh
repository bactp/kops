# Must FAIL: pods run, but the Service still targets the wrong port.
kubectl -n {{ns}} create serviceaccount {{sa}}
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"volumes":[{"name":"site","configMap":{"name":"{{app}}-conf"}}]}}}}'
