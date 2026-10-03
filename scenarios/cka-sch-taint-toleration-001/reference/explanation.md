# Taint and toleration

## Root cause
The node's `NoSchedule` taint repels pods that do not tolerate it; the Deployment selects the node but has no toleration, so the scheduler reports `node(s) had untolerated taint`.

## Approach
Add a toleration `{key: dedicated, operator: Equal, value: {{team}}, effect: NoSchedule}` to the pod template and keep the nodeSelector, which pins the pods to the dedicated node (a toleration only permits, it does not attract).

## What the verifier checks
Two Running pods, all on nodes matching `dedicated={{team}}`; the node still has the `dedicated` taint with effect NoSchedule.

## Why shortcuts fail
Removing the taint trips the guard; a toleration without the nodeSelector lets pods spread to the other worker.
