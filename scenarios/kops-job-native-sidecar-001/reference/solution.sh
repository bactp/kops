# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get cronjob {{app}} -o yaml
kubectl -n {{ns}} patch cronjob {{app}} --type json -p '[{"op":"remove","path":"/spec/jobTemplate/spec/template/spec/containers/1"},{"op":"add","path":"/spec/jobTemplate/spec/template/spec/initContainers","value":[{"name":"shipper","image":"busybox:1.36.1","imagePullPolicy":"IfNotPresent","restartPolicy":"Always","command":["sleep","3600"]}]}]'
kubectl -n {{ns}} create job {{job}} --from=cronjob/{{app}}
kubectl -n {{ns}} wait --for=condition=complete job/{{job}} --timeout=60s
