In namespace `{{ns}}`, the `{{app}}` application is up: its pods are Ready and its Service has endpoints.
Still, requests to `http://{{app}}.{{ns}}.svc.cluster.local/` (Service port 80) from other pods hang and time out, although the name resolves.

Find the cause somewhere else in the cluster and fix it, so the Service answers again.

Do not delete the component you find at fault or its configuration objects.
