# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} describe pvc {{app}}-claim
kubectl get pv {{app}}-vol -o yaml
kubectl patch pv {{app}}-vol -p '{"spec":{"capacity":{"storage":"2Gi"},"accessModes":["ReadWriteOnce"],"storageClassName":"{{sc}}"}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
