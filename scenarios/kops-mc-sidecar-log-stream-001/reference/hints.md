# Hints
1. Containers in a pod can share a volume. Which volume already holds the log file?
2. The sidecar needs the same volume mounted at the same path and a command that keeps printing the file (`tail -F`).
3. Patch the pod template to add container `{{sc}}` (image `busybox:1.36.1`) with `volumeMounts: logs -> /var/log/app` and command `tail -n+1 -F /var/log/app/app.log`.
