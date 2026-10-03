# Hints
1. `kubectl create priorityclass --help` shows `--value` and `--global-default`.
2. Pods choose a class with `spec.priorityClassName` in the pod template. Changing the template rolls the pods.
3. Create the class, patch `spec.template.spec.priorityClassName`, and check a pod's `spec.priority`.
