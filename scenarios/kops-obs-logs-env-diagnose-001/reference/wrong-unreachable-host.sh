# Must FAIL: the variable is set, but to a host that does not exist, so the app exits with code 4.
kubectl -n {{ns}} set env deployment/{{app}} CACHE_HOST=localhost
