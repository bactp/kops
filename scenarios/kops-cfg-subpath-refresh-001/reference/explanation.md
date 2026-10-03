# ConfigMap change not visible through a subPath mount

## Root cause
Kubernetes refreshes ConfigMap volumes in running pods, except for files mounted with `subPath`. The Deployment mounts a single key with `subPath`,
so patching the ConfigMap leaves the existing pods serving the old file until they are replaced.

## Approach
1. `kubectl -n {{ns}} patch configmap {{app}}-page --type merge -p '{"data":{"index.html":"{{new}}"}}'`
2. Notice the page did not change (or know about the subPath caveat) and `kubectl -n {{ns}} rollout restart deployment/{{app}}`.
3. `kubectl rollout status deployment/{{app}}`.

## What the verifier checks
HTTP body equals the new text five times, the ConfigMap key holds the new text, rollout complete, ConfigMap UID unchanged.

## Why shortcuts fail
Editing alone leaves old pods serving the old text; restarting alone re-reads the unchanged ConfigMap; deleting and re-creating the ConfigMap fails the UID guard.
