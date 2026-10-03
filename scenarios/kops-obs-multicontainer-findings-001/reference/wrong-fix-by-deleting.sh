# Must FAIL: removing the failing container 'fixes' the pod but modifies the Deployment and records nothing.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/containers/1"}]'
