# Must FAIL: an empty egress rule lets the client reach everything, including the {{other}} service.
kubectl -n {{ns}} patch networkpolicy client-egress --type merge -p '{"spec":{"egress":[{}]}}'
