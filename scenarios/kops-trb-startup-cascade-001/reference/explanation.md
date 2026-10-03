# Layered start-up failure

## Faults in the order they appear
1. No pods exist: `kubectl describe replicaset` shows `error looking up service account {{ns}}/{{sa}}: serviceaccount "{{sa}}" not found`. Fix: `kubectl create serviceaccount {{sa}}` (pointing the Deployment at `default` would also be acceptable).
2. Pods stay `ContainerCreating`: `describe pod` shows `MountVolume.SetUp failed ... configmap "{{app}}-config" not found`. Fix: patch the volume to ConfigMap `{{app}}-conf`.
3. Pods are Ready but the Service has no working backend: its `targetPort` is {{port2}}, the app listens on {{port}}. Fix: patch `targetPort`.

## What the verifier checks
Three HTTP requests through the Service return the greeting from the ConfigMap, the rollout is complete, and the ConfigMap is unchanged.

## Why shortcuts fail
Each fix alone leaves a later fault in place.
