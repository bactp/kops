# Must FAIL: the pods spread out by luck of the default scheduler, but nothing enforces the spread.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/nodeSelector"}]'
