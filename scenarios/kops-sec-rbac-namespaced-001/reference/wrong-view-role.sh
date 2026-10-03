# Must FAIL: the built-in view ClusterRole bound in the namespace also exposes deployments and more than asked.
kubectl -n {{ns}} create rolebinding {{sa}}-view --clusterrole=view --serviceaccount={{ns}}:{{sa}}
