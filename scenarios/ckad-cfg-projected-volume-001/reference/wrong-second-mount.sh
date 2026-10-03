# Must FAIL: mounting the Secret at another path leaves token.txt out of /etc/site.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"add","path":"/spec/template/spec/volumes/-","value":{"name":"tok","secret":{"secretName":"{{app}}-token"}}},{"op":"add","path":"/spec/template/spec/containers/0/volumeMounts/-","value":{"name":"tok","mountPath":"/etc/tok"}}]'
