# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl create clusterrole {{cr}} --verb=get,list,watch --resource=nodes
kubectl patch clusterrole {{cr}} --type json -p '[{"op":"add","path":"/rules/-","value":{"apiGroups":[""],"resources":["persistentvolumes"],"verbs":["get","list"]}}]'
kubectl create clusterrolebinding {{cr}} --clusterrole={{cr}} --serviceaccount={{ns}}:{{sa}}
