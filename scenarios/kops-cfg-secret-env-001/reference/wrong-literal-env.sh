# Must FAIL: works functionally but puts the password into the pod template as a literal.
kubectl -n {{ns}} set env deployment/{{app}} DB_USERNAME={{user}} DB_PASSWORD={{pw}}
