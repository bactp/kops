# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pvc
kubectl get pv
kubectl patch pv {{app}}-pv-{{d}} -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
