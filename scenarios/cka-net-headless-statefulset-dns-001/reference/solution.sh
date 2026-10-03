# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get service,statefulset
kubectl -n {{ns}} delete service {{svc}}
kubectl -n {{ns}} create service clusterip {{svc}} --clusterip=None --tcp=80:{{port}}
