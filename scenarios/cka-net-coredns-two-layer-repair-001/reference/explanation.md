# Two broken layers of cluster DNS

## Root cause
1. `kube-dns` selects `k8s-app=kube-dns-legacy`, so it has no endpoints and queries to the cluster DNS IP time out.
2. After that is fixed, the Corefile's `kubernetes` plugin serves `cluster.lcl` rather than `cluster.local`, so `*.svc.cluster.local` answers NXDOMAIN.

## Approach
1. From a pod `nslookup` times out: check the CoreDNS pods (Running) then the Service (`get endpoints kube-dns` is empty; the selector does not match the pods' labels). Patch the selector back to `k8s-app: kube-dns`.
2. Lookups now fail with NXDOMAIN: read the `coredns` ConfigMap, spot `cluster.lcl`, and patch the Corefile (the whole file is one ConfigMap key, so the patch carries the full text).
3. CoreDNS has the `reload` plugin and picks the change up within about 30 s; `rollout restart deployment/coredns` makes it immediate.

## What the verifier checks
`nslookup kubernetes.default.svc.cluster.local` from a probe pod returns 10.96.0.1; `kube-dns` has a ready endpoint on port 53; the Corefile still contains `forward . /etc/resolv.conf`; the `kube-dns` UID and ClusterIP are unchanged.

## Why shortcuts fail
Fixing either layer alone leaves resolution failing (timeout or NXDOMAIN).
