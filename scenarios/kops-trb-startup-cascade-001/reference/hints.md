# Hints
1. There are no pods at all. Which object creates pods, and where would it report why it cannot?
2. After the first fix the pods stay in `ContainerCreating`. Their events tell you which volume source is missing; list what really exists in the namespace.
3. Create the missing ServiceAccount, point the volume at the existing ConfigMap, then check `kubectl get endpoints` and the Service's `targetPort` against the port the app listens on.
