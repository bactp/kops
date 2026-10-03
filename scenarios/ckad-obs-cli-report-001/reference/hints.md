# Hints
1. `kubectl get pods --sort-by=...` orders by any field. Which timestamp tells you when a pod was created?
2. `-o custom-columns` lets you show a field such as a container's memory request next to the pod name.
3. `--field-selector=status.phase!=Running` lists the pods that are not running. Create the ConfigMap with `--from-literal` for each answer.
