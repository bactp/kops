# Must FAIL: the Job is created from the still-broken template and never completes; the CronJob itself is not repaired.
kubectl -n {{ns}} create job {{job}} --from=cronjob/{{app}}-report
