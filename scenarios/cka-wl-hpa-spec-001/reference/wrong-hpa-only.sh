# Must FAIL: the HPA exists but the container has no CPU request.
kubectl -n {{ns}} autoscale deployment {{app}} --min={{min}} --max={{max}} --cpu={{cpu}}%
