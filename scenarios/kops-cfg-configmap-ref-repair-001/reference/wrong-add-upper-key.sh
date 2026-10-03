# Must FAIL: adding a LOG_LEVEL key to the ConfigMap alters its data (guard) and leaves the MODE reference broken.
kubectl -n {{ns}} patch configmap {{app}}-settings --type merge -p '{"data":{"LOG_LEVEL":"{{level}}"}}'
