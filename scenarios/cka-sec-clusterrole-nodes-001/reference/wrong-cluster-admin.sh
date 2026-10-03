# Must FAIL: cluster-admin allows far more than asked.
kubectl create clusterrole {{cr}} --verb=get --resource=nodes
kubectl create clusterrolebinding {{cr}}-admin --clusterrole=cluster-admin --serviceaccount={{ns}}:{{sa}}
