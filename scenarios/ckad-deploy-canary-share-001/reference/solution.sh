# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get deployments,service --show-labels
kubectl -n {{ns}} scale deployment/{{app}}-stable --replicas=3
kubectl -n {{ns}} scale deployment/{{app}}-canary --replicas=1
kubectl -n {{ns}} patch service {{app}} --type json -p '[{"op":"remove","path":"/spec/selector/track"}]'
kubectl -n {{ns}} rollout status deployment/{{app}}-canary --timeout=120s
