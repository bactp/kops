# Must FAIL: the CronJob is configured but no run was triggered.
kubectl -n {{ns}} create cronjob {{app}} --image=busybox:1.36.1 --schedule="{{sched}}" -- sh -c "echo {{marker}}"
kubectl -n {{ns}} patch cronjob {{app}} -p '{"spec":{"concurrencyPolicy":"Forbid","successfulJobsHistoryLimit":2,"failedJobsHistoryLimit":1}}'
