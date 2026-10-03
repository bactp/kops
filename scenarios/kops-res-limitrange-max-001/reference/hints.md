# Hints
1. No pods exist, so look at the ReplicaSet's events. The message quotes the policy it violated.
2. `kubectl get limitrange -o yaml` shows the allowed range. Your pod's limit must be inside it.
3. `kubectl set resources deployment/<name> --requests=memory=<m> --limits=memory=<n>` with n between the min and max.
