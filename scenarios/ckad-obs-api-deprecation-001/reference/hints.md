# Hints
1. Which API versions does this cluster actually serve? `kubectl api-versions` and `kubectl api-resources` answer that.
2. Four kinds are affected, each in a different API group. Look for the group/version that is stable for it today.
3. Patch the ConfigMap data so that each manifest keeps its kind and body but starts with the served apiVersion (`autoscaling/v2`, `policy/v1`, `batch/v1`, `flowcontrol.apiserver.k8s.io/v1`).
