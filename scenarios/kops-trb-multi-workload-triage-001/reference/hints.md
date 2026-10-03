# Hints
1. Start with `kubectl get pods`: each broken application shows a different status. Use `describe` and `logs` per failure.
2. Three unrelated causes: something about an image, something about a start command, something about where pods may run.
3. `kubectl set image` for the tag, a patch of the container command for the crash loop, and removing the impossible nodeSelector for the Pending pods.
