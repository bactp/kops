# Must FAIL: the pods run but only because the namespace policy was weakened.
kubectl label namespace {{ns}} pod-security.kubernetes.io/enforce=privileged --overwrite
