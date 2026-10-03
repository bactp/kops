# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl get nodes
kubectl describe nodes
kubectl uncordon -l hold=cordon
kubectl taint nodes -l hold=taint {{key}}-
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
