# HPA with a CPU target

## Approach
`kubectl autoscale deployment {{app}} --min={{min}} --max={{max}} --cpu={{cpu}}%` creates the HPA. A CPU *utilisation* target is relative to the pods' CPU request, so give the container one:
`kubectl set resources deployment/{{app}} --requests=cpu=100m`.

## What the verifier checks
HPA scale target (kind Deployment, name), `minReplicas`, `maxReplicas`, the Resource metric's `averageUtilization`; the container's `requests.cpu` exists; Deployment UID unchanged.
**Spec-only**: there is no metrics-server on this backend, so scale-up/down behaviour and the `ScalingActive` condition are not tested (see docs/scenario-backlog.md).

## Why shortcuts fail
An HPA on a Deployment without CPU requests can never compute utilisation; wrong bounds fail the spec checks.
