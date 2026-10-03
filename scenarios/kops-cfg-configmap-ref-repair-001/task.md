Pods of the `{{app}}` Deployment in namespace `{{ns}}` never start (they report a container configuration error).
The application is supposed to take its `SETTING` and `MODE` values from the ConfigMap that already exists in the namespace
and publish them at `http://{{app}}.{{ns}}.svc.cluster.local/` as `<SETTING> <MODE>` on one line.

Get the Deployment healthy so that this works, using the values stored in the existing ConfigMap.

Constraints:
- Do not change the values stored in the ConfigMap.
- Do not copy the values into the Deployment as literals.
