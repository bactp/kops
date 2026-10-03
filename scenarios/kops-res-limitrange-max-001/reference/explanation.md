# LimitRange maximum

## Root cause
The namespace LimitRange allows container memory between 64Mi and {{max}}Mi. The Deployment requests 800Mi / limits 1Gi, so the ReplicaSet gets
`forbidden: maximum memory usage per Container is {{max}}Mi, but limit is 1Gi` and creates no pods.

## Approach
`kubectl describe replicaset` shows the message; `kubectl get limitrange -o yaml` the bounds. `kubectl set resources deployment/{{app}} --requests=memory=100Mi --limits=memory=200Mi` (any limit in [64Mi, {{max}}Mi]; the request must not exceed the limit).

## What the verifier checks
Rollout complete with two Running pods; `limits.memory` between 64Mi and {{max}}Mi; LimitRange spec and UID unchanged; replicas 2.

## Why shortcuts fail
Deleting or raising the LimitRange fails its guard.
