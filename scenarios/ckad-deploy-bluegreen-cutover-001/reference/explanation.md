# Blue/green cutover

## Approach
1. `kubectl -n {{ns}} scale deployment/{{app}}-green --replicas=3` and wait (`rollout status`) until all green pods are ready.
2. Only then move the Service: `kubectl patch service {{app}} -p '{"spec":{"selector":{"app":"{{app}}","track":"green"}}}'`.
Blue stays at 3 replicas so switching the selector back is an instant rollback.

## What the verifier checks
Five requests return `green-{{v2}}`; three ready green pods; blue still at 3 replicas with the same UID; Service UID/ClusterIP unchanged.

## Why shortcuts fail
Switching the selector before green runs yields no endpoints. Deleting or scaling down blue removes the rollback path.
