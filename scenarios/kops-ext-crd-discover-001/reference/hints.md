# Hints
1. `kubectl get crd` shows which extension types exist. `kubectl api-resources` has columns for group, short names and kind.
2. The phase is a field inside each object's `spec`. `-o custom-columns` or `-o jsonpath` can show it for all objects at once.
3. `kubectl create configmap ext-inventory -n {{ns}} --from-literal=kind=... --from-literal=apiGroup=... --from-literal=shortName=... --from-literal=ready=...`.
