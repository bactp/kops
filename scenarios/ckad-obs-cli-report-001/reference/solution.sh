# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods --sort-by=.metadata.creationTimestamp
kubectl -n {{ns}} get pods -o custom-columns=NAME:.metadata.name,MEM:.spec.containers[0].resources.requests.memory,PHASE:.status.phase
kubectl -n {{ns}} create configmap pod-report --from-literal=oldest={{pre}}-1 --from-literal=largestMemoryRequest={{pre}}-{{bigidx}} --from-literal=notRunning={{nfail}}
