# Hints
1. Two separate settings are involved: which ServiceAccount the pods use, and whether its token is mounted into them.
2. `kubectl set serviceaccount` handles the first. The second is a field of the pod spec.
3. Create the account, `kubectl set serviceaccount deployment/<name> <sa>`, then patch `spec.template.spec.automountServiceAccountToken` to `false`.
