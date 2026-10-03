# Must FAIL: a second headless Service leaves {{svc}} itself with a single cluster IP.
kubectl -n {{ns}} create service clusterip {{svc}}-headless --clusterip=None --tcp=80:{{port}}
