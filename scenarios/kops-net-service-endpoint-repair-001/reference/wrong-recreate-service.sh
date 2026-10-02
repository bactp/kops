# Must FAIL: traffic works again but the Service was deleted and re-created (UID/ClusterIP guard).
kubectl -n {{ns}} delete service {{app}}
kubectl -n {{ns}} create service clusterip {{app}} --tcp=80:{{port}}
