# Namespaced read-only RBAC

## Approach
A Role lists verbs per resource; a RoleBinding attaches it to the ServiceAccount. Two Roles keep verbs exact (watch is wanted for pods only):
- `kubectl create role {{sa}}-reader --verb=get,list,watch --resource=pods`
- `kubectl create role {{sa}}-logs-extra --verb=get,list --resource=pods/log,{{extra}}`
- `kubectl create rolebinding ... --role=... --serviceaccount={{ns}}:{{sa}}` for each.
(One Role with a broader verb set would also pass: the checks are about what is allowed and what is denied, not about the number of objects.)

## What the verifier checks
`kubectl auth can-i --as=system:serviceaccount:{{ns}}:{{sa}}` allows the six requested operations and denies: delete/create pods, get secrets,
list deployments, list pods in `kube-system`, list nodes.

## Why shortcuts fail
Binding `cluster-admin` or the built-in `view` ClusterRole passes the allow checks but fails the deny checks (view can list deployments; cluster-admin can do everything).
