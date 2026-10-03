# Must FAIL: Secret is created but the Deployment does not consume it.
kubectl -n {{ns}} create secret generic {{app}}-db --from-literal=username={{user}} --from-literal=password={{pw}}
