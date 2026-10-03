# Must FAIL: the main port is repaired but the admin port still maps to the http container port.
kubectl -n {{ns}} patch service {{app}} --type merge -p '{"spec":{"ports":[{"name":"http","port":80,"targetPort":"http"},{"name":"admin","port":9090,"targetPort":{{port}}}]}}'
