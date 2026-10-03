# Must FAIL: without the policy the client is unrestricted.
kubectl -n {{ns}} delete networkpolicy client-egress
