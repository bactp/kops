# Reclaim policy of the volume behind a claim

## Approach
The reclaim policy belongs to the PersistentVolume, not to the claim. `kubectl get pvc` (VOLUME column) shows that `{{app}}-data` is bound to `{{app}}-pv-{{d}}`.
`kubectl patch pv {{app}}-pv-{{d}} -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'`.

## What the verifier checks
PV `{{app}}-pv-{{d}}` has `Retain`; PV `{{app}}-pv-{{c}}` still `Delete`; both claims Bound.

## Why shortcuts fail
Changing both volumes or the wrong one fails the guard or the goal.
