The ServiceAccount `{{sa}}` in namespace `{{ns}}` runs an inventory exporter. It must be able to
- `get`, `list` and `watch` Nodes, and
- `get` and `list` PersistentVolumes,
across the whole cluster. Use a ClusterRole named `{{cr}}`.

Nothing else may be allowed: no changes to nodes, no access to Secrets, no creating Pods.
