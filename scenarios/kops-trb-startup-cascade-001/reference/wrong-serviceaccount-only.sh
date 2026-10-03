# Must FAIL: the pods are created but stay in ContainerCreating on the missing ConfigMap.
kubectl -n {{ns}} create serviceaccount {{sa}}
