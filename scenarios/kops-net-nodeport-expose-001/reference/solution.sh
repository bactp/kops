# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get deployment {{app}} --show-labels
kubectl -n {{ns}} expose deployment {{app}} --name={{app}}-public --type=NodePort --port=80 --target-port={{port}}
kubectl -n {{ns}} patch service {{app}}-public --type json -p '[{"op":"replace","path":"/spec/ports/0/nodePort","value":{{np}}}]'
