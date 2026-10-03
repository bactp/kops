# Must FAIL: pointing at the app's own Service is not the cache.
kubectl -n {{ns}} set env deployment/{{app}} CACHE_HOST={{app}}-cache
