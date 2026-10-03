# Hints
1. How many revisions does each `kubectl set ...` command create? `kubectl rollout history` shows them.
2. You can tell the controller to wait while you edit the template.
3. `kubectl rollout pause`, apply the three changes, `kubectl rollout resume`, then `rollout status`.
