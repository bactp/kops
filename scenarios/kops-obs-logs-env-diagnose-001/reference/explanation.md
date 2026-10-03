# Logs show the missing setting

## Approach
`kubectl logs deployment/{{app}}` (or `--previous`) prints `fatal: CACHE_HOST is not set`. The value is the name of the cache Service: `kubectl get services` shows `{{cache}}`.
`kubectl set env deployment/{{app}} CACHE_HOST={{cache}}` and wait for the rollout. Note that a wrong value changes the log message (`cannot reach cache at ...`, exit code 4).

## What the verifier checks
Three HTTP requests through the Service return `cache-reachable` and the rollout is complete; cache Deployment and Service are unchanged.

## Why shortcuts fail
Any unreachable value makes the app exit before it serves.
