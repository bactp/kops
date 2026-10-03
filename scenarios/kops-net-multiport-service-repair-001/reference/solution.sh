# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get service {{app}} -o yaml
kubectl -n {{ns}} get endpoints {{app}}
kubectl -n {{ns}} get deployment {{app}} -o jsonpath={.spec.template.spec.containers[0].ports}
kubectl -n {{ns}} patch service {{app}} --type merge -p '{"spec":{"ports":[{"name":"http","port":80,"targetPort":"http"},{"name":"admin","port":9090,"targetPort":"admin"}]}}'
