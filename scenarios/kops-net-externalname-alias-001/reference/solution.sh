# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl get services --all-namespaces
kubectl -n {{ns}} create service externalname {{alias}} --external-name={{svc}}.{{ns}}-data.svc.cluster.local
