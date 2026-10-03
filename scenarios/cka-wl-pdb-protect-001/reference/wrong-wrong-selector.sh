# Must FAIL: a selector on the conventional app label matches no pods, so the budget protects nothing.
kubectl -n {{ns}} create poddisruptionbudget {{app}}-pdb --selector=app={{app}} --max-unavailable=1
