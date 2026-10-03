In namespace `{{ns}}`, the `{{app}}` application is protected by NetworkPolicies, but its legitimate clients
(pods labelled `role={{cl}}`) can no longer call it at `http://{{app}}.{{ns}}.svc.cluster.local/` (Service port 80).

Repair the policies so those clients get through again.

Constraints:
- Pods that are not `role={{cl}}` clients (for example a pod labelled `role=scanner`) must remain unable to reach `{{app}}`.
- Keep the namespace-wide default-deny policy in place.
