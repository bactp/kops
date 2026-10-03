# A claim that cannot bind

## Root cause
A claim binds to a volume only if the class matches, the volume offers at least the requested capacity, and its access modes include the requested ones.
The PV has class `archive` (claim: `{{sc}}`), 1Gi (claim: 2Gi) and `ReadOnlyMany` (claim: `ReadWriteOnce`).

## Approach
`kubectl describe pvc` shows the Pending event; `kubectl get pv {{app}}-vol -o yaml` shows the volume. Patch the PV (these fields are mutable): `capacity.storage: 2Gi`, `accessModes: [ReadWriteOnce]`, `storageClassName: {{sc}}`.
The binder re-evaluates and binds; the pod then starts.

## What the verifier checks
The claim is Bound with `volumeName {{app}}-vol`; the rollout is complete; the claim's UID and spec are unchanged; the PV keeps its UID and `Retain` policy.

## Why shortcuts fail
Deleting the claim breaks the application team's request. Fixing only one attribute leaves the claim Pending.
