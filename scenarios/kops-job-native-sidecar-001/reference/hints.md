# Hints
1. When does a Job's pod count as finished? What would have to happen to `shipper`?
2. Kubernetes has a first-class way to run a helper container next to the main one and stop it automatically: look for `restartPolicy` on init containers.
3. JSON-patch the CronJob's pod template: remove `shipper` from `containers`, add it to `initContainers` with `restartPolicy: Always`. Then `kubectl create job ... --from=cronjob/...`.
