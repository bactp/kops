# Must FAIL: deleting the DaemonSet removes the component altogether.
kubectl -n kube-system delete daemonset kube-proxy
