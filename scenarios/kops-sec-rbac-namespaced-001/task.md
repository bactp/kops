The ServiceAccount `{{sa}}` in namespace `{{ns}}` is used by a monitoring job. Give it read-only access, in this namespace only, to:
- pods: `get`, `list` and `watch`
- the logs of pods (`pods/log`): `get`
- `{{extra}}`: `get` and `list`

Nothing else should be allowed. In particular it must not be able to modify anything,
read Secrets, or see anything outside `{{ns}}`.
