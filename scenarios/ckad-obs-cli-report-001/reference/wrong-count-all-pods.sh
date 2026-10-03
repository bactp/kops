# Must FAIL: counting all pods instead of the ones not Running gives the wrong notRunning value.
kubectl -n {{ns}} create configmap pod-report --from-literal=oldest={{pre}}-1 --from-literal=largestMemoryRequest={{pre}}-{{bigidx}} --from-literal=notRunning=5
