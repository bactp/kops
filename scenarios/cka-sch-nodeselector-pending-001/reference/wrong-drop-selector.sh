# Must FAIL: without any selector pods spread over both workers, including the general node.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/nodeSelector"}]'
