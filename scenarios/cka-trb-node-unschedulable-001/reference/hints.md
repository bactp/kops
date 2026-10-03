# Hints
1. `kubectl get nodes` and `kubectl describe pod` (events) tell you what each node reports. There are two different mechanisms.
2. One node shows `SchedulingDisabled`; the other has a custom taint (`kubectl describe node`). There is a command for each.
3. `kubectl uncordon <node>` and `kubectl taint nodes <node> <key>-` (the dash removes it). Leave the control-plane node alone.
