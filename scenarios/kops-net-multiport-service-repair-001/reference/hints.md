# Hints
1. `kubectl get endpoints` and `kubectl describe service` show whether each port resolved to something. What names and numbers do the container's ports use?
2. A named `targetPort` must equal a container port name exactly.
3. Patch the Service ports: 80 -> `http`, 9090 -> `admin` (or the admin port number). Keep the port names.
