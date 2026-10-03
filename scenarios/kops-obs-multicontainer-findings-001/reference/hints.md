# Hints
1. A pod with several containers reports each container's status separately. `kubectl describe pod` shows them all.
2. Look for the container whose last state is `Terminated` with a non-zero exit code. `kubectl logs -c <name> --previous` shows its output.
3. Create the ConfigMap with `kubectl create configmap {{app}}-findings --from-literal=container=<name> --from-literal=exitCode=<code>`.
