# Must FAIL: scaling to two replicas and cordoning avoids moving pods but drops capacity (replica guard).
kubectl cordon -l maintenance=scheduled
kubectl -n {{ns}} scale deployment/{{app}} --replicas=2
