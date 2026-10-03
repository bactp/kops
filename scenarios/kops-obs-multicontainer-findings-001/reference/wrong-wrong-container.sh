# Must FAIL: recording the main container instead of the one that fails.
kubectl -n {{ns}} create configmap {{app}}-findings --from-literal=container=web --from-literal=exitCode={{code}}
