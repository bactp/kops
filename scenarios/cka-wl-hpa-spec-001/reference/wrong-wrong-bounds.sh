# Must FAIL: min and max are swapped for fixed numbers that do not match the request.
kubectl -n {{ns}} set resources deployment/{{app}} --requests=cpu=100m
kubectl -n {{ns}} autoscale deployment {{app}} --min=1 --max=3 --cpu={{cpu}}%
