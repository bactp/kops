# Must FAIL: a Service with the right name but a selector that matches no pods resolves in DNS but has no endpoints.
kubectl -n {{ns}} create service clusterip {{dep}} --tcp={{dport}}:{{dport}}
