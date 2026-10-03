Namespace `{{ns}}` contains five bare pods named `{{pre}}-1` to `{{pre}}-5`. Use kubectl to answer these questions and record the answers
in a ConfigMap named `pod-report` in the same namespace:
- `oldest`: the name of the pod that was created first
- `largestMemoryRequest`: the name of the pod with the largest memory request
- `notRunning`: how many of the pods are not in phase `Running` (digits only)

Do not modify or delete any pod.
