Service `{{app}}` in namespace `{{ns}}` has no ready endpoints, and the pods of its Deployment also keep restarting.
The application itself works: it answers `GET /healthz` on port {{port}}.

Repair the Deployment so that both replicas are Ready, stop restarting, and the Service has two ready endpoints.
The Deployment must keep both a readiness probe and a liveness probe.
