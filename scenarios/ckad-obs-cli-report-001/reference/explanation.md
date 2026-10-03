# Output shaping with kubectl

## Approach
- Oldest: `kubectl get pods --sort-by=.metadata.creationTimestamp` (first row).
- Largest memory request: `kubectl get pods -o custom-columns=NAME:.metadata.name,MEM:.spec.containers[0].resources.requests.memory` (or `-o jsonpath` / `describe`).
- Not Running: `kubectl get pods` STATUS column / `--field-selector=status.phase!=Running` and count the rows.
Then `kubectl create configmap pod-report --from-literal=...`.

## What the verifier checks
The three keys equal the values set up for this seed; all five pods still exist.

## Why shortcuts fail
Pod names suggest an order, but the request sizes and phases are what matter; deleting pods violates the guard.
