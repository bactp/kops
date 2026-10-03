# Create a CronJob and run it

## Approach
1. `kubectl create cronjob {{app}} --image=busybox:1.36.1 --schedule="{{sched}}" -- sh -c "echo {{marker}}"`
2. `kubectl patch cronjob {{app}} -p '{"spec":{"concurrencyPolicy":"Forbid","successfulJobsHistoryLimit":2,"failedJobsHistoryLimit":1}}'` (the imperative create has no flags for these).
3. `kubectl create job {{app}}-now --from=cronjob/{{app}}` and `kubectl wait --for=condition=complete job/{{app}}-now`.

## What the verifier checks
Schedule, image, `Forbid`, history limits 2/1, and the on-demand Job is Complete with `{{marker}}` in its log.

## Why shortcuts fail
Skipping the policy patch leaves `Allow` and default limits (3/1); skipping the run leaves no Job.
