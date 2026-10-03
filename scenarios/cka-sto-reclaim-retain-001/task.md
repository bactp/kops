Namespace `{{ns}}` has two claims, `{{app}}-data` (valuable) and `{{app}}-cache` (disposable), each bound to a pre-provisioned PersistentVolume
whose reclaim policy is currently `Delete`.

Make sure that if the claim `{{app}}-data` is ever deleted, the volume behind it and its data are kept.
Change only what is needed: the volume behind `{{app}}-cache` must keep its current policy, and both claims must stay bound.
