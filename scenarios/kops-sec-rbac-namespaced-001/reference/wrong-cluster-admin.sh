# Must FAIL: cluster-admin satisfies the reads but destroys least privilege.
kubectl create clusterrolebinding {{sa}}-admin --clusterrole=cluster-admin --serviceaccount={{ns}}:{{sa}}
