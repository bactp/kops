The CI job that runs as ServiceAccount `{{sa}}` in namespace `{{ns}}` gets `Forbidden` whenever it tries to
list Deployments, patch them, or scale them. It is supposed to be able to do exactly this in `{{ns}}`:
`get`, `list` and `patch` on Deployments, and `update` on the `scale` subresource of Deployments.

A Role and a RoleBinding for this already exist in the namespace, but the grant does not work. Make it work.

Constraints:
- Do not grant anything beyond what is listed (no delete, no Secrets, nothing outside `{{ns}}`).
