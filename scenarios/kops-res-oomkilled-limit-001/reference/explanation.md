# OOMKilled container

## Root cause
The app allocates roughly 40 MB of data at start-up, plus runtime overhead. The memory limit is 64Mi, so the kernel OOM-killer terminates the container
(`lastState.terminated.reason: OOMKilled`, exit code 137) and the kubelet restarts it in a loop (CrashLoopBackOff).

## Approach
1. `kubectl -n {{ns}} get pods` shows restarts; `kubectl describe pod` shows `Last State: Terminated, Reason: OOMKilled`.
2. Raise the limit with `kubectl set resources deployment/{{app}} --limits=memory=160Mi --requests=memory=64Mi` (any value that fits the working set and stays at or below `{{cap}}`; 128Mi works with margin).
3. Wait for the rollout; the new pods must stay up.

## What the verifier checks
Both pods are Ready in five samples over 20 seconds, current pods have zero restarts, limits.memory exists and is at most `{{cap}}`, replicas still 2.

## Why shortcuts fail
Removing the limit or setting 2Gi stops the kills but violates the explicit policy guard.
