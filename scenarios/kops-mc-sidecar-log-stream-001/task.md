The `{{app}}` Deployment in namespace `{{ns}}` writes its log to a file, `/var/log/app/app.log`, on an `emptyDir` volume called `logs`.
The log collection agent only reads container stdout, so these lines are invisible to it.

Add a sidecar container named `{{sc}}` (image `busybox:1.36.1`) to the pod that shares the volume and prints the file's content
to its own stdout continuously, so `kubectl logs ... -c {{sc}}` shows the application's lines.

Do not change the main container.
