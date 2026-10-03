# Must FAIL: the ExternalName points to a name that does not exist.
kubectl -n {{ns}} create service externalname {{alias}} --external-name={{svc}}.{{ns}}.svc.cluster.local
