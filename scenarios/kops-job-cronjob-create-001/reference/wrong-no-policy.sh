# Must FAIL: the CronJob exists and runs, but concurrency and history limits keep their defaults.
kubectl -n {{ns}} create cronjob {{app}} --image=busybox:1.36.1 --schedule="{{sched}}" -- sh -c "echo {{marker}}"
kubectl -n {{ns}} create job {{app}}-now --from=cronjob/{{app}}
