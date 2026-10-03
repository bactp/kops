# Hints
1. Pods are not being created at all. Where would an admission rejection be reported? Try `kubectl describe replicaset` or the events.
2. The message lists every field that violates the profile. Check the Kubernetes docs page on Pod Security Standards for the restricted fields.
3. Set runAsNonRoot + a non-zero runAsUser + seccompProfile RuntimeDefault on the pod, and allowPrivilegeEscalation=false + drop ALL on the container.
