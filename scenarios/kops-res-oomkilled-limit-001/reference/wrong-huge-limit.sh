# Must FAIL: a 2Gi limit stops the kills but exceeds the policy cap.
kubectl -n {{ns}} set resources deployment/{{app}} --limits=memory=2Gi
