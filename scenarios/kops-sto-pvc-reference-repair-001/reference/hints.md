# Hints
1. The pod's events say which object it cannot find. Compare the name with `kubectl get pvc`.
2. Two claims exist. One of them is Bound: that is the one that was used before and holds the data.
3. Patch the Deployment's volume `data` so that `persistentVolumeClaim.claimName` is `{{app}}-data`.
