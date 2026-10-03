# Hints
1. After you apply the settings, watch the new pods. Do they stay up? `kubectl logs` tells you why not.
2. A read-only root filesystem still allows writes to mounted volumes. What directory does the start-up command write to?
3. Add an `emptyDir` volume mounted at `/tmp` together with the securityContext fields (user and runAsNonRoot on the pod, the other three on the container).
