# Must FAIL: a ClusterIP Service named like the alias has no endpoints, so the client cannot connect.
kubectl -n {{ns}} create service clusterip {{alias}} --tcp=80:{{port}}
