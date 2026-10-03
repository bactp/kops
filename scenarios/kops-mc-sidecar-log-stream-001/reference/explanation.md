# Log-streaming sidecar

## Approach
A pod's containers share volumes declared in the pod spec. The `logs` emptyDir already exists; mount it into a second container that runs `tail -n+1 -F /var/log/app/app.log`, whose stdout is then collected as that container's log.
One strategic-merge patch adds the container (containers merge by `name`), then `rollout status`.

## What the verifier checks
A container named `{{sc}}` with the pinned image exists; its logs contain at least three `event N` lines; the main container's image, mount and command are unchanged.

## Why shortcuts fail
Without the volume mount `tail` waits for a file that never appears in that container's filesystem and prints nothing.
