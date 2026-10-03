# Hints
1. Reproduce the failure with `kubectl auth can-i ... --as=system:serviceaccount:<ns>:<sa>` and look at the Role and the RoleBinding side by side.
2. Two things must line up: the rule must name the API group the resource lives in (`kubectl api-resources` shows it), and the binding subject must name the ServiceAccount's real namespace.
3. Patch the Role rules so both use apiGroup `apps`, and set the RoleBinding subject namespace to `{{ns}}`. Re-run can-i.
