The `{{app}}` Deployment in namespace `{{ns}}` is crash-looping. Use the pod's logs to find out what it needs, and fix it.

The application is correct; only its configuration is incomplete. When it works, the Service `{{app}}` (port 80)
answers with the body `cache-reachable`.

Constraint: do not modify the cache Deployment or Service in the namespace.
