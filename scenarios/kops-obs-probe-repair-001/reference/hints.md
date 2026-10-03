# Hints
1. `kubectl describe pod` lists the probe failures. There are two different kinds, with different consequences.
2. Compare each probe's target (path, port) with what the application actually serves.
3. Patch the container: readiness `httpGet /healthz` on port {{port}}, liveness on port {{port}} too (a TCP check is fine). Do not remove them.
