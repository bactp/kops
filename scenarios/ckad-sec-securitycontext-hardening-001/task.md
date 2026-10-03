The `{{app}}` Deployment in namespace `{{ns}}` runs as root with full filesystem access. Harden its pods:
- run as non-root, user id `{{uid}}`
- read-only root filesystem
- no privilege escalation
- drop all Linux capabilities

The application must keep working afterwards: the Deployment has to roll out cleanly and Service `{{app}}`
(port 80) must keep answering with HTTP 200.
