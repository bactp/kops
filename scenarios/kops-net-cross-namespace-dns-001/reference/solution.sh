# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} logs deployment/client --tail=5
kubectl get services --all-namespaces
kubectl -n {{ns}} set env deployment/client TARGET=http://{{svc}}.{{ns}}-backend.svc.cluster.local/
kubectl -n {{ns}} rollout status deployment/client --timeout=120s
