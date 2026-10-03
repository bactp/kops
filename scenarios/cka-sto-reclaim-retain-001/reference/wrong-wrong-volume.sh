# Must FAIL: the volume of the disposable claim was changed instead of the data volume.
kubectl patch pv {{app}}-pv-{{c}} -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
