# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} describe pods
kubectl get nodes --show-labels
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"nodeSelector":{"pool":"{{pool}}"}}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
