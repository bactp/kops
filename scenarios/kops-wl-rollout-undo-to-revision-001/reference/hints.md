# Hints
1. Compare what is running with what the rollout is trying to run. `kubectl rollout status` and `kubectl get pods` tell you why it is stuck.
2. Not every healthy revision is the right one. Look at what each revision of the pod template contains: `kubectl rollout history deployment/<name> --revision=<n>`.
3. `kubectl rollout undo` accepts a `--to-revision` flag. Pick the revision whose environment says the banner is `{{color}}-1`, then wait for the rollout.
