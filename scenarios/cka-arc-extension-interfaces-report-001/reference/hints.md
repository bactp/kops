# Hints
1. `kubectl get nodes -o wide` shows more than status: look at the runtime column.
2. Pod networking add-ons usually run as a DaemonSet in `kube-system`. A StorageClass names its provisioner.
3. `kubectl create configmap cluster-interfaces -n {{ns}} --from-literal=runtime=... --from-literal=cni=... --from-literal=provisioner=... --from-literal=kubelet=...`
