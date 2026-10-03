The `{{app}}` Deployment in namespace `{{ns}}` is running but not reachable by anything.
Expose it with a Service named `{{app}}-public`:
- type `NodePort`
- Service port 80, forwarding to the port the containers listen on
- node port `{{np}}`

When you are done, the Service must have ready endpoints and answer HTTP requests.

Constraint: do not modify the Deployment.
