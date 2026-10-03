# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} create role {{sa}}-reader --verb=get,list,watch --resource=pods
kubectl -n {{ns}} create role {{sa}}-logs-extra --verb=get,list --resource=pods/log,{{extra}}
kubectl -n {{ns}} create rolebinding {{sa}}-reader --role={{sa}}-reader --serviceaccount={{ns}}:{{sa}}
kubectl -n {{ns}} create rolebinding {{sa}}-logs-extra --role={{sa}}-logs-extra --serviceaccount={{ns}}:{{sa}}
