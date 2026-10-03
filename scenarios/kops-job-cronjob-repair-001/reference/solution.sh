# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get cronjob,jobs,pods
kubectl -n {{ns}} patch cronjob {{app}}-report -p '{"spec":{"jobTemplate":{"spec":{"template":{"spec":{"containers":[{"name":"report","image":"busybox:1.36.1"}]}}}}}}'
kubectl -n {{ns}} create job {{job}} --from=cronjob/{{app}}-report
kubectl -n {{ns}} wait --for=condition=complete job/{{job}} --timeout=60s
