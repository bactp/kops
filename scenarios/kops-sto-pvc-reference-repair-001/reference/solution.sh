# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} describe pods
kubectl -n {{ns}} get pvc
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"{{app}}-data"}}]}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
