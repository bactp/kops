# Pod Security `restricted`

## Root cause
The restricted profile requires: `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, all capabilities dropped, and a `seccompProfile` of `RuntimeDefault` or `Localhost`.
The Deployment sets none of them, so the ReplicaSet gets `forbidden: violates PodSecurity "restricted:latest"` (visible in `kubectl describe replicaset`).

## Approach
Read the rejection message and patch the pod template: pod securityContext `{runAsNonRoot: true, runAsUser: 10001, seccompProfile: {type: RuntimeDefault}}`,
container securityContext `{allowPrivilegeEscalation: false, capabilities: {drop: [ALL]}}`. Then wait for the rollout.

## What the verifier checks
Rollout complete, two Running pods, HTTP 200 with the expected body, and the namespace `enforce` label is still `restricted`.

## Why shortcuts fail
Relabelling the namespace to `privileged` makes pods start but trips the policy guard. A partial context is still rejected.
