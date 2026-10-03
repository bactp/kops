# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} set resources deployment/{{app}} --requests=cpu=100m
kubectl -n {{ns}} autoscale deployment {{app}} --min={{min}} --max={{max}} --cpu={{cpu}}%
