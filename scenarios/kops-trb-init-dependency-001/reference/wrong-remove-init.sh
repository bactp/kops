# Must FAIL: deleting the init container starts the pods but defeats the dependency gate.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/initContainers"}]'
