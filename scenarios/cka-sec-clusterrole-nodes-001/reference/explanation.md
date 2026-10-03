# Cluster-scoped read access

## Approach
Nodes and PersistentVolumes are cluster-scoped, so the grant needs a ClusterRole plus a ClusterRoleBinding.
`kubectl create clusterrole {{cr}} --verb=get,list,watch --resource=nodes`, add the persistentvolumes rule
(`kubectl patch clusterrole ... --type json` or create a second ClusterRole and bind it too; the name `{{cr}}` must exist),
then `kubectl create clusterrolebinding {{cr}} --clusterrole={{cr}} --serviceaccount={{ns}}:{{sa}}`.

## What the verifier checks
can-i allow for the five reads, ClusterRole `{{cr}}` exists, deny for patch/delete nodes, Secrets in kube-system, creating pods.

## Why shortcuts fail
A namespaced RoleBinding to the ClusterRole is accepted by the API but never authorizes cluster-scoped resources. cluster-admin fails the deny checks.
