# Hints
1. Is a Node a namespaced object? The answer decides which kind of binding you need.
2. `kubectl api-resources --namespaced=false` lists cluster-scoped resources. `kubectl create clusterrole` and `kubectl create clusterrolebinding` take `--verb`, `--resource`, `--serviceaccount=<ns>:<name>`.
3. Create ClusterRole `{{cr}}` for nodes (get, list, watch) and persistentvolumes (get, list), then a ClusterRoleBinding to the ServiceAccount. Verify with `kubectl auth can-i`.
