Workloads in this cluster can no longer resolve in-cluster names: a lookup of `kubernetes.default.svc.cluster.local` from a pod does not return an address.
Cluster DNS (CoreDNS in `kube-system`) is the suspect.

Find out what is wrong and restore name resolution for the cluster domain.

Constraints:
- Keep forwarding of other names to the node's resolver (`/etc/resolv.conf`) as it is configured today.
- Do not delete and re-create the `kube-dns` Service (keep its ClusterIP).
