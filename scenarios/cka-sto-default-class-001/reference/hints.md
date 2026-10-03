# Hints
1. A default class is marked with an annotation on the StorageClass. `kubectl get storageclass` shows `(default)`.
2. Two classes marked default is an error for claims that omit the class.
3. Patch/annotate both classes: `standard` loses the annotation (or gets "false"), `{{sc}}` gets `storageclass.kubernetes.io/is-default-class: "true"`.
