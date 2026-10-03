A platform team installed an extension API into this cluster; its objects live in namespace `{{ns}}`. You were not told what it is called.

Discover it and write down the facts in a ConfigMap named `ext-inventory` in namespace `{{ns}}`, with these keys:
- `kind`: the Kind of the custom resource
- `apiGroup`: its API group
- `shortName`: its short name
- `ready`: the number of objects in `{{ns}}` whose `spec.phase` is `Ready`

This is an inspection task: do not modify or delete any of the custom resources.
