# Must FAIL: pods are restarted but the ConfigMap still holds the old text.
kubectl -n {{ns}} rollout restart deployment/{{app}}
