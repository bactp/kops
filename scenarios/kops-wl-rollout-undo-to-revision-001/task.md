The `{{app}}` service in namespace `{{ns}}` is in trouble: its most recent update never finished rolling out.

Management wants customers served again by the release that announced itself with the banner `{{color}}-1`
(the banner is the body of the page the Service returns on port 80).
Get the `{{app}}` Deployment back to that release and make sure the rollout completes.

Constraints:
- Do not delete and re-create the Deployment.
- Keep the replica count unchanged.
