The `client` Deployment in namespace `{{ns}}` calls the `{{svc}}` service every couple of seconds and logs `OK` or `FAIL` for each call.
`{{svc}}` runs in the namespace `{{ns}}-backend`. Right now the client's log shows only failures.

Make the client's calls succeed (its most recent log lines must show `OK` and no `FAIL`).

Constraint: do not modify or move anything in `{{ns}}-backend`.
