# Hints
1. Mounting two volumes at the same path does not merge them. Is there a volume type that merges several sources?
2. The Secret's file name defaults to its key. `items` lets you choose a path.
3. JSON-patch-replace the volume with `projected.sources`: the ConfigMap, and the Secret with `items: [{key: token, path: token.txt}]`.
