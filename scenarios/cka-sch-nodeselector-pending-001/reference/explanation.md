# nodeSelector with no matching node

## Root cause
The pod template asks for `pool={{pool}}-v2`; the node is labelled `pool={{pool}}`. The scheduler reports `0/3 nodes are available: ... didn't match Pod's node affinity/selector`.

## Approach
`kubectl describe pod` (events), `kubectl get nodes --show-labels` to find the real label, then patch the nodeSelector (`{"pool":"{{pool}}"}`); the merge replaces the value.

## What the verifier checks
3 Running pods, every one on a node that matches `pool={{pool}}`; node labels unchanged (exactly one node per pool value); replicas still 3.

## Why shortcuts fail
Relabelling nodes violates the node-label guard. Removing the selector places pods on the general node too.
