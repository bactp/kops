# Hints
1. The failure happens before any HTTP exchange. What must a pod do before it can connect to a Service by name?
2. DNS is served by pods in `kube-system` on port 53 (UDP and TCP). An egress policy has to permit that traffic explicitly.
3. Append an egress rule to the existing policy with a `namespaceSelector` for `kube-system` and ports 53/UDP and 53/TCP. Keep the existing rule.
