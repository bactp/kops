# Must FAIL: the Job completes, but the sidecar was removed instead of converted.
kubectl -n {{ns}} patch cronjob {{app}} --type json -p '[{"op":"remove","path":"/spec/jobTemplate/spec/template/spec/containers/1"}]'
kubectl -n {{ns}} create job {{job}} --from=cronjob/{{app}}
