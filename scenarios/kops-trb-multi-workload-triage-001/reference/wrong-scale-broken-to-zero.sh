# Must FAIL: scaling the broken Deployments to zero makes them 'healthy' but they no longer serve and replicas changed.
kubectl -n {{ns}} scale deployment/{{b}} deployment/{{c}} deployment/{{d}} --replicas=0
