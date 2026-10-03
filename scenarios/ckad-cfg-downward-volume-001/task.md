The `{{app}}` Deployment in namespace `{{ns}}` serves the files in `/etc/podinfo` over HTTP (Service port 80). That directory is supposed
to describe the pod itself:
- a file `labels` with the pod's labels
- a file `namespace` with the pod's namespace

Right now the directory is empty. Fix the Deployment so that
`http://{{app}}.{{ns}}.svc.cluster.local/labels` and `.../namespace` return that information, using the downward API.
Keep the same image and mount path.
