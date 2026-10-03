# Must FAIL: the sidecar exists but does not mount the shared volume, so it never sees the file.
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"containers":[{"name":"{{sc}}","image":"busybox:1.36.1","imagePullPolicy":"IfNotPresent","command":["sh","-c","tail -n+1 -F /var/log/app/app.log"]}]}}}}'
