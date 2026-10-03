# Must FAIL: the node stops accepting pods, but the running ones are not evicted.
kubectl cordon -l maintenance=scheduled
