# Hints
1. `kubectl describe pod` shows exactly what the kubelet could not resolve. Expect more than one defect.
2. Compare the names and keys used by the Deployment with what `kubectl get configmap -o yaml` shows. Keys are case sensitive.
3. Patch the two `configMapKeyRef` entries of the `web` container (name `{{app}}-settings`, keys `log_level` and `mode`) and wait for the rollout.
