# Hints
1. Is CoreDNS itself running? Then check how clients reach it: the `kube-dns` Service and its endpoints.
2. If lookups return an answer like NXDOMAIN instead of timing out, the DNS server is reachable but not serving that domain. Read the `coredns` ConfigMap.
3. Fix the Service selector to match the CoreDNS pod labels, then correct the domain in the `kubernetes` line of the Corefile (`cluster.local`). Restart CoreDNS or wait for the reload.
