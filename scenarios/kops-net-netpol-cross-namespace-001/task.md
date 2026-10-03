The `{{app}}` service in namespace `{{ns}}` (Service port 80) is protected by NetworkPolicies that only admit traffic from inside the namespace.

The team that owns namespace `{{ns}}-partner` needs to call it at `http://{{app}}.{{ns}}.svc.cluster.local/`.
Allow that namespace in, and nothing more:
- pods in `{{ns}}-other` must stay blocked,
- pods inside `{{ns}}` must keep working,
- keep the default-deny policy.
