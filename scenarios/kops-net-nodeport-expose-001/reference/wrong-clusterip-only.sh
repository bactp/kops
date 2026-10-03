# Must FAIL: the default Service type is ClusterIP, which is not a NodePort.
kubectl -n {{ns}} expose deployment {{app}} --name={{app}}-public --port=80 --target-port={{port}}
