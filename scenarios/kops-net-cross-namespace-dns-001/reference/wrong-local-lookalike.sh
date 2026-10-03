# Must FAIL: a same-named Service in the client namespace has no endpoints, so calls still fail (and the guard objects).
kubectl -n {{ns}} create service clusterip {{svc}} --tcp=80:{{port}}
