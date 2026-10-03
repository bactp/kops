# Hints
1. Look at the pod's last termination state (`kubectl describe pod`). The reason and exit code identify the failure class.
2. The container needs more memory than its limit allows, but the task caps how far you may go.
3. `kubectl set resources deployment/<name> --limits=memory=<value>`; a value between roughly 128Mi and the cap works. Wait for the rollout afterwards.
