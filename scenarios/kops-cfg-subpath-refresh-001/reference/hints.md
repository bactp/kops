# Hints
1. After you update the stored configuration, ask the running application what it serves. Does it match?
2. Look at how the Deployment mounts the ConfigMap. One field there changes how updates propagate.
3. Patch the ConfigMap value, then roll the pods with `kubectl rollout restart deployment/<name>` and wait for completion.
