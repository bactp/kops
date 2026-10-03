# Hints
1. `kubectl create service --help` lists the Service types you can create imperatively.
2. Which type maps a Service name to another DNS name instead of to pods?
3. `kubectl create service externalname <alias> --external-name=<service>.<namespace>.svc.cluster.local` in the client namespace.
