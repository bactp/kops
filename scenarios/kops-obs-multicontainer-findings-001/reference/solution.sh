# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods
kubectl -n {{ns}} describe pods
kubectl -n {{ns}} logs deployment/{{app}} -c {{bad}} --previous
kubectl -n {{ns}} create configmap {{app}}-findings --from-literal=container={{bad}} --from-literal=exitCode={{code}}
