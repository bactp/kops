# Must FAIL: the DaemonSet reaches the control plane only because its taint was removed.
kubectl taint nodes -l node-role.kubernetes.io/control-plane node-role.kubernetes.io/control-plane:NoSchedule-
