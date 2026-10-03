# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl create priorityclass {{pc}} --value={{val}} --description="critical workloads"
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"priorityClassName":"{{pc}}"}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
