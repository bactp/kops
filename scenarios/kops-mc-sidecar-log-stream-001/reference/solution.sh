# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get deployment {{app}} -o yaml
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"containers":[{"name":"{{sc}}","image":"busybox:1.36.1","imagePullPolicy":"IfNotPresent","command":["sh","-c","tail -n+1 -F /var/log/app/app.log"],"volumeMounts":[{"name":"logs","mountPath":"/var/log/app"}]}]}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
