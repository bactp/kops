For an architecture review, record how this cluster is plugged together. Create a ConfigMap named `cluster-interfaces` in namespace `{{ns}}` with the keys:
- `runtime`: the container runtime and version exactly as the nodes report it (the value of the container runtime version of a node)
- `cni`: the name of the DaemonSet in `kube-system` that provides pod networking
- `provisioner`: the provisioner of the StorageClass that is the cluster default
- `kubelet`: the kubelet version the nodes report

Only read from the cluster; do not change anything in `kube-system`.
