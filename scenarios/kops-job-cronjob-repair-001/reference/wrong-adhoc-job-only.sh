# Must FAIL: an ad-hoc Job completes and prints the line, but the CronJob template is still broken.
kubectl -n {{ns}} create job {{job}} --image=busybox:1.36.1 -- sh -c 'echo {{marker}}'
