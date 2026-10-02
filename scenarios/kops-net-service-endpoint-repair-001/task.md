The `{{app}}` application in namespace `{{ns}}` is not reachable through its Service.

Restore access so that clients inside the cluster can reach
`http://{{app}}.{{ns}}.svc.cluster.local/healthz` on port 80.

Constraints:
- Do not modify the Deployment's pod template.
- Do not delete and re-create the Service; keep its name and ClusterIP.
