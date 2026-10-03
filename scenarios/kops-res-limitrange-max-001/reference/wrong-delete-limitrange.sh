# Must FAIL: deleting the policy lets the pods in, but the policy is not ours to remove.
kubectl -n {{ns}} delete limitrange {{app}}-limits
