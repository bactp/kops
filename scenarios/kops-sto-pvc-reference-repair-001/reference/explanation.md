# Wrong claim reference

## Root cause
The pod template mounts claim `{{app}}-state`, which does not exist: the pod is `Pending` with `persistentvolumeclaim "{{app}}-state" not found`.
Two claims exist: `{{app}}-data` (Bound, contains the state file) and `{{app}}-scratch` (empty, `Pending` until something uses it).

## Approach
`kubectl get pvc` shows which claim is Bound (it was used by the earlier run). Patch the volume `data` to reference `{{app}}-data`; wait for the rollout.

## What the verifier checks
Three HTTP requests return `keep-{{marker}}` from `/state.txt`; rollout complete; `{{app}}-data` is still Bound with unchanged UID/spec; the scratch claim is unchanged.

## Why shortcuts fail
The empty claim or an emptyDir both start the app without the data (404 for /state.txt).
