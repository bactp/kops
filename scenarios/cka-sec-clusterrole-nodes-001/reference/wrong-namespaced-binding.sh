# Must FAIL: a RoleBinding to a ClusterRole only grants namespaced access, so cluster-scoped Nodes stay forbidden.
kubectl create clusterrole {{cr}} --verb=get,list,watch --resource=nodes,persistentvolumes
kubectl -n {{ns}} create rolebinding {{cr}} --clusterrole={{cr}} --serviceaccount={{ns}}:{{sa}}
