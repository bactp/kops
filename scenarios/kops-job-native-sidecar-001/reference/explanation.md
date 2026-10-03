# Native sidecar for a Job

## Root cause
A Job's pod completes only when **all regular containers** have terminated. `shipper` is a regular container that sleeps for an hour, so the Job hangs.

## Approach
Native sidecars (Kubernetes 1.29+, stable in 1.33) are init containers with `restartPolicy: Always`: they start before `main`, keep running next to it, and are stopped when the regular containers finish.
JSON-patch the CronJob: remove `containers/1` and add `initContainers: [{name: shipper, ..., restartPolicy: Always}]`. Then `kubectl create job {{job}} --from=cronjob/{{app}}` and `kubectl wait --for=condition=complete job/{{job}}`.

## What the verifier checks
`shipper` is an init container with `restartPolicy: Always` and no longer a regular container; `main` is still regular; Job `{{job}}` is Complete and `kubectl logs job/{{job}} -c main` has the marker; the CronJob UID and schedule are unchanged.

## Why shortcuts fail
Deleting the sidecar completes the Job but loses the sidecar; running before the fix hangs.
