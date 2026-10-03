# Hints
1. Access is granted by a Role (what) plus a RoleBinding (to whom). Both are namespaced here.
2. `kubectl create role --help` shows `--verb` and `--resource`; a subresource is written `pods/log`. `kubectl auth can-i ... --as=system:serviceaccount:<ns>:<name>` lets you test.
3. Create a Role with exactly the requested verbs/resources and a RoleBinding with `--serviceaccount=<namespace>:<name>`. Avoid cluster-wide roles.
