# Migrating removed API versions

## Approach
Find what the cluster serves: `kubectl api-versions` (lists group/versions) and `kubectl api-resources` (kind -> API version). For the four kinds the stable versions are
`autoscaling/v2`, `policy/v1`, `batch/v1` and `flowcontrol.apiserver.k8s.io/v1`. The old betas were removed in earlier releases. Rewrite the four manifests inside the ConfigMap (one merge patch can carry all four keys).

## What the verifier checks
**Data-only check** (the manifests are not applied): each key has the expected `apiVersion:` line and still the original `kind:` line. For `PodDisruptionBudget`/`CronJob` the manifests are otherwise valid in the new version; the HPA v2 manifest uses the same fields.

## Why shortcuts fail
Migrating only some keys or choosing an older served version (`autoscaling/v1`) fails the per-key checks; deleting a manifest trips the kind guard.
