The claim `{{app}}-claim` in namespace `{{ns}}` is stuck in `Pending`, and the `{{app}}` Deployment that mounts it cannot start.
A PersistentVolume named `{{app}}-vol` was prepared for this claim, but they do not match.

Get the claim bound to `{{app}}-vol` and the Deployment running. The claim is requested by the application team
and must not be changed, deleted or re-created: correct the volume instead.
