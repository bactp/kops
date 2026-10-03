The `{{app}}` Deployment in namespace `{{ns}}` serves files from a persistent volume, but its pod is stuck Pending.
An earlier run of the application saved its state (the file `/state.txt`) on a claim that still exists in the namespace.

Get the application running on the claim that holds that data, so that
`http://{{app}}.{{ns}}.svc.cluster.local/state.txt` returns the saved content.

Constraint: do not delete or modify the existing claims.
