# Must FAIL: raising the maximum changes the platform team's policy.
kubectl -n {{ns}} patch limitrange {{app}}-limits --type merge -p '{"spec":{"limits":[{"type":"Container","min":{"memory":"64Mi"},"max":{"memory":"2Gi"}}]}}'
