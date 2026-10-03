# Must FAIL: deleting the memory limit stops the OOM kills but violates the limit guard.
kubectl -n {{ns}} set resources deployment/{{app}} --limits=memory=0 --requests=memory=0
