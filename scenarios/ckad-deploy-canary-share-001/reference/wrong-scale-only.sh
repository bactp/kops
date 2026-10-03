# Must FAIL: canary pods exist but the Service still selects track=stable, so the canary never receives traffic.
kubectl -n {{ns}} scale deployment/{{app}}-stable --replicas=3
kubectl -n {{ns}} scale deployment/{{app}}-canary --replicas=1
