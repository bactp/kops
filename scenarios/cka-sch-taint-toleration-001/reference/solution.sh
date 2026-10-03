# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} describe pods
kubectl describe nodes
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"tolerations":[{"key":"dedicated","operator":"Equal","value":"{{team}}","effect":"NoSchedule"}]}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
