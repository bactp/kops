The `{{app}}` application in namespace `{{ns}}` was deployed but nothing works: no pods are running, and clients cannot get a page from
Service `{{app}}` (port 80).

Make it work. When it does, the Service returns the greeting stored in the namespace's ConfigMap (its `index.html` key)
and both replicas are ready.

Constraint: keep the existing ConfigMap and its content.
