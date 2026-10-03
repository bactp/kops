# Discovering a custom resource type

## Approach
`kubectl get crd` lists the extension; `kubectl api-resources --api-group=<group>` (or `describe crd`) shows kind, group, scope and short names.
`kubectl -n {{ns}} get {{short}} -o custom-columns=NAME:.metadata.name,PHASE:.spec.phase` lists the objects and their phase (or use `-o jsonpath`); count those with `Ready`.
Record the facts with `kubectl create configmap ext-inventory --from-literal=...`.

## What the verifier checks
The ConfigMap's four keys equal the true values (`ready` = {{nready}}); the four custom resources still exist.

## Why shortcuts fail
Counting all objects gives the wrong number; deleting objects violates the inspection-only guard.
