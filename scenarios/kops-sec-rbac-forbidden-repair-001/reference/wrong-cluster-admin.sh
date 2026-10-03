# Must FAIL: cluster-admin makes every call work and breaks least privilege.
kubectl create clusterrolebinding {{sa}}-admin --clusterrole=cluster-admin --serviceaccount={{ns}}:{{sa}}
