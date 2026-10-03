# Hints
1. Read the client's logs and find out where the backend Service really is (`kubectl get svc --all-namespaces`).
2. DNS names of Services have the form `<service>.<namespace>.svc.cluster.local`. A bare service name resolves only in the caller's own namespace.
3. Change the client's `TARGET` environment variable to the namespaced name (`kubectl set env deployment/client TARGET=...`) and wait for the new pod.
