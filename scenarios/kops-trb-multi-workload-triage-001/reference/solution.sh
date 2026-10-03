# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods
kubectl -n {{ns}} describe pods
kubectl -n {{ns}} set image deployment/{{b}} web=busybox:1.36.1
kubectl -n {{ns}} patch deployment {{c}} -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","command":["sh","-c","mkdir -p /tmp/w && echo {{c}}-ok > /tmp/w/index.html && exec httpd -f -p {{port}} -h /tmp/w"]}]}}}}'
kubectl -n {{ns}} patch deployment {{d}} --type json -p '[{"op":"remove","path":"/spec/template/spec/nodeSelector"}]'
kubectl -n {{ns}} rollout status deployment/{{b}} --timeout=120s
kubectl -n {{ns}} rollout status deployment/{{c}} --timeout=120s
kubectl -n {{ns}} rollout status deployment/{{d}} --timeout=120s
