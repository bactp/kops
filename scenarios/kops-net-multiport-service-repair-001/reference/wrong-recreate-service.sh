# Must FAIL: deleting and re-creating the Service changes its UID and ClusterIP.
kubectl -n {{ns}} delete service {{app}}
kubectl -n {{ns}} expose deployment {{app}} --port=80 --target-port=http
