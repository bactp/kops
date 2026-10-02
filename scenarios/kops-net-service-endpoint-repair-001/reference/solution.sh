# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get service {{app}} -o yaml
kubectl -n {{ns}} get pods --show-labels
kubectl -n {{ns}} patch service {{app}} --type merge -p '{"spec":{"selector":{"app":"{{app}}","tier":"web"},"ports":[{"port":80,"targetPort":{{port}}}]}}'
