# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} logs deployment/client --tail=5
kubectl -n {{ns}} get deployment client -o yaml
kubectl -n {{ns}} patch deployment client -p '{"spec":{"template":{"spec":{"dnsPolicy":"ClusterFirstWithHostNet"}}}}'
kubectl -n {{ns}} rollout status deployment/client --timeout=120s
