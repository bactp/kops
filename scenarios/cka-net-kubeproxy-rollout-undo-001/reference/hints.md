# Hints
1. Endpoints exist, DNS resolves, but connections hang. Which cluster component turns a Service IP into pod IPs on each node?
2. Check that component's pods in `kube-system` and the DaemonSet's recent history.
3. `kubectl -n kube-system rollout undo daemonset/kube-proxy`, then wait for the rollout and test the Service again.
