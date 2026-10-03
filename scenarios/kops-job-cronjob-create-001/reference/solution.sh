# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} create cronjob {{app}} --image=busybox:1.36.1 --schedule="{{sched}}" -- sh -c "echo {{marker}}"
kubectl -n {{ns}} patch cronjob {{app}} -p '{"spec":{"concurrencyPolicy":"Forbid","successfulJobsHistoryLimit":2,"failedJobsHistoryLimit":1}}'
kubectl -n {{ns}} create job {{app}}-now --from=cronjob/{{app}}
kubectl -n {{ns}} wait --for=condition=complete job/{{app}}-now --timeout=60s
