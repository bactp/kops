# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl describe nodes
kubectl -n {{ns}} get daemonset {{app}}
kubectl -n {{ns}} patch daemonset {{app}} -p '{"spec":{"template":{"spec":{"tolerations":[{"key":"node-role.kubernetes.io/control-plane","operator":"Exists","effect":"NoSchedule"}]}}}}'
kubectl -n {{ns}} rollout status daemonset/{{app}} --timeout=120s
