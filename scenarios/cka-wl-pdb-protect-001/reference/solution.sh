# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get deployment {{app}} --show-labels
kubectl -n {{ns}} get pods --show-labels
kubectl -n {{ns}} create poddisruptionbudget {{app}}-pdb --selector=component={{app}} --max-unavailable=1
