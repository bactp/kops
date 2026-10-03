# Hardening with a securityContext

## Approach
Pod-level: `runAsNonRoot: true`, `runAsUser: {{uid}}`. Container-level: `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: ["ALL"]`.
The start-up script writes `/tmp/site`, which fails on a read-only root filesystem, so mount an `emptyDir` volume at `/tmp`.
One strategic-merge patch can do all of it; then `rollout status`.

## What the verifier checks
Behaviour, not field names: the app's page reports what the running process sees. The verifier requires `uid={{uid}} nnp=1 capbnd=0000000000000000 rootfs=ro` five times through the Service
(non-root uid, no_new_privs set, empty capability bounding set, read-only root), plus a clean rollout. Pod-level and container-level settings are therefore equally valid.

## Why shortcuts fail
Without the writable volume the container crashes (CrashLoopBackOff), so the rollout never completes and HTTP checks fail. A partial context fails the field checks.
