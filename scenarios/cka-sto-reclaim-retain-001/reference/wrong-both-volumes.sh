# Must FAIL: both volumes are switched to Retain, but the disposable cache volume must keep Delete.
kubectl patch pv {{app}}-pv-{{d}} -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
kubectl patch pv {{app}}-pv-{{c}} -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
