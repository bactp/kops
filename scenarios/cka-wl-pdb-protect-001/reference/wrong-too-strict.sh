# Must FAIL: minAvailable=4 allows zero disruptions, which blocks maintenance entirely.
kubectl -n {{ns}} create poddisruptionbudget {{app}}-pdb --selector=component={{app}} --min-available=4
