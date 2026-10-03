# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl get nodes --show-labels
kubectl -n {{ns}} get pods -o wide
kubectl drain -l maintenance=scheduled --ignore-daemonsets --delete-emptydir-data
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
