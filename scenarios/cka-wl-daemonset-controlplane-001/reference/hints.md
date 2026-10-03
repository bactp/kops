# Hints
1. How many nodes does the cluster have, and where does the DaemonSet run? What keeps it off the control plane?
2. `kubectl describe node <control-plane>` shows its taints. A taint is bypassed with a toleration in the pod template.
3. Patch the DaemonSet's `spec.template.spec.tolerations` with key `node-role.kubernetes.io/control-plane`, operator `Exists`, effect `NoSchedule`.
