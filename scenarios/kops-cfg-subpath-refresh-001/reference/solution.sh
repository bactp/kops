# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} patch configmap {{app}}-page --type merge -p '{"data":{"index.html":"{{new}}"}}'
kubectl -n {{ns}} rollout restart deployment/{{app}}
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
