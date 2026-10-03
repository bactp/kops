# Must FAIL: all traffic is moved to the canary instead of a quarter.
kubectl -n {{ns}} scale deployment/{{app}}-canary --replicas=4
kubectl -n {{ns}} scale deployment/{{app}}-stable --replicas=0
kubectl -n {{ns}} patch service {{app}} --type json -p '[{"op":"remove","path":"/spec/selector/track"}]'
