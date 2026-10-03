# Slow start vs liveness probe

## Root cause
The liveness probe starts at 2 s and tolerates 2 failures at a 3 s period, so the kubelet kills the container at roughly 8 s. The app needs {{delay}} s.

## Approach
Add a `startupProbe` on the same endpoint with a generous budget (`periodSeconds: 5`, `failureThreshold: 12` = 60 s). Liveness and readiness probes do not run until the startup probe has succeeded.
(Raising `liveness.initialDelaySeconds` above the start time is also valid, but it delays failure detection forever; the startup probe is the idiomatic fix.)

## What the verifier checks
Both pods are Ready in four samples over 15 s, current pods have 0 restarts, the liveness probe still targets `/healthz`, and replicas are still 2.

## Why shortcuts fail
Removing the liveness probe violates the guard. A 10 s initial delay is still shorter than the start-up time, so pods keep restarting.
