# Repair the CronJob, then trigger it

## Root cause
`jobTemplate` references `busybox:1.36.11`, which does not exist, so pods of every Job from this CronJob sit in `ErrImagePull`/`ImagePullBackOff`.

## Approach
1. Patch the CronJob's container image to `busybox:1.36.1` (strategic merge keyed on the container name `report`).
2. `kubectl create job {{job}} --from=cronjob/{{app}}-report` copies the (now fixed) template into a new Job.
3. `kubectl wait --for=condition=complete job/{{job}}`; `kubectl logs job/{{job}}` shows `{{marker}}`.

## What the verifier checks
CronJob image fixed; Job `{{job}}` has condition Complete and its log has the marker; CronJob UID, schedule, concurrencyPolicy and suspend unchanged.

## Why shortcuts fail
An ad-hoc `create job --image` does not repair the CronJob. Creating the Job before fixing copies the broken template.
