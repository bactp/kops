# Must FAIL: the Service has endpoints again, but the Corefile still serves cluster.lcl, so lookups return NXDOMAIN.
kubectl -n kube-system patch service kube-dns --type merge -p '{"spec":{"selector":{"k8s-app":"kube-dns"}}}'
