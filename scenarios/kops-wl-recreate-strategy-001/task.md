The `{{app}}` Deployment in namespace `{{ns}}` currently serves the banner `v1`. Each replica takes an exclusive lock on startup,
so during an update the old pods must be fully gone before any new pod is created.

Configure the Deployment accordingly and then roll out the new release, which is the same image with `MSG` set to `{{ver}}`.
When you are done, clients must get the banner `{{ver}}` from Service `{{app}}` on port 80 and all three replicas must be ready.

Constraints:
- Keep 3 replicas.
- Do not delete the Deployment.
