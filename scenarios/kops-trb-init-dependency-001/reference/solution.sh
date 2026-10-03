# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods
kubectl -n {{ns}} logs deployment/{{app}} -c wait-for-dependency
kubectl -n {{ns}} get deployments,services
kubectl -n {{ns}} expose deployment {{dep}}-server --name={{dep}} --port={{dport}}
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
