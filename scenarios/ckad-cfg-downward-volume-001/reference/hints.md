# Hints
1. The downward API can project pod metadata into files through a volume of type `downwardAPI`.
2. A volume has exactly one source. What does the existing `podinfo` volume use today?
3. JSON-patch-replace the volume with `downwardAPI.items`: path `labels` -> `metadata.labels`, path `namespace` -> `metadata.namespace`.
