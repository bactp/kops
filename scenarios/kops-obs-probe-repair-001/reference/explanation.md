# Two broken probes

## Root cause
- Readiness requests `/ready`, which returns 404, so the pod never joins the Service endpoints.
- Liveness opens TCP port {{port2}}, which nothing listens on, so the kubelet restarts the container (with `failureThreshold: 1`, within seconds).

## Approach
`describe pod` shows `Readiness probe failed: HTTP probe failed with statuscode: 404` and `Liveness probe failed: ... connection refused` on port {{port2}}. Patch both probes to the real endpoint/port and wait for the rollout.

## What the verifier checks
Two ready endpoints on {{port}}, zero restarts over a 20 s window, HTTP 200 with the app's body, and both probes still present.

## Why shortcuts fail
Deleting the probes trips the guard; fixing only readiness leaves the restart loop.
