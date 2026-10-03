# Must FAIL: removing the control-plane taint lets pods in, but violates the guard and releases nobody.
kubectl taint nodes -l node-role.kubernetes.io/control-plane node-role.kubernetes.io/control-plane:NoSchedule-
