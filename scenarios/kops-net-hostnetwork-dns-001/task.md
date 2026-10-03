The `client` Deployment in namespace `{{ns}}` calls the Service `{{svc}}` (same namespace) every couple of seconds by its short name,
and logs `OK` or `FAIL` for each call. Right now its log shows only `FAIL`, although `{{svc}}` itself is healthy.

The client has to run on the **host network** of its node (it needs to see the node's interfaces), so that setting must stay.
Make the client's calls succeed (its most recent log lines must show `OK` and no `FAIL`) without changing the target name or the backend.
