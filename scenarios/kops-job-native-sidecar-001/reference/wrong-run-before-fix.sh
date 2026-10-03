# Must FAIL: the Job is created from the unchanged template and never completes.
kubectl -n {{ns}} create job {{job}} --from=cronjob/{{app}}
