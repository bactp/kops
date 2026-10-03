# Hints
1. Is the reclaim policy a property of the claim or of the volume? Find which volume backs the data claim (`kubectl get pvc`).
2. PersistentVolumes are cluster-scoped. `kubectl patch pv <name> -p '{"spec":{...}}'` edits them.
3. Set `persistentVolumeReclaimPolicy` to `Retain` on the volume bound to `{{app}}-data` only.
