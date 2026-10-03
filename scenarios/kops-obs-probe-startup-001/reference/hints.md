# Hints
1. `kubectl describe pod` shows liveness probe failures and restarts. When do they begin compared to the start-up time?
2. There is a dedicated probe type for slow starters that holds off the other probes until the app is up.
3. Add a `startupProbe` (httpGet `/healthz`, period 5 s, failureThreshold 12) to the container; keep the liveness probe.
