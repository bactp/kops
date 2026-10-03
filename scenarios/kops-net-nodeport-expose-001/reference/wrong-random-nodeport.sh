# Must FAIL: a NodePort Service is created but with an arbitrary node port.
kubectl -n {{ns}} expose deployment {{app}} --name={{app}}-public --type=NodePort --port=80 --target-port={{port}}
