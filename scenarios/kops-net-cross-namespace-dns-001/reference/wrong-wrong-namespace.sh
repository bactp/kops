# Must FAIL: pointing at the client's own namespace does not reach the backend.
kubectl -n {{ns}} set env deployment/client TARGET=http://{{svc}}.{{ns}}.svc.cluster.local/
