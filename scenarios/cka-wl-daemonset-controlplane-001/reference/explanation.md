# DaemonSet and the control-plane taint

## Root cause
kubeadm-style control-plane nodes carry `node-role.kubernetes.io/control-plane:NoSchedule`. A DaemonSet pod is only created there if its template tolerates the taint.

## Approach
`kubectl describe node` shows the taint. Patch the DaemonSet template with a toleration (`key: node-role.kubernetes.io/control-plane, operator: Exists, effect: NoSchedule`) and wait for the rollout.

## What the verifier checks
`desiredNumberScheduled` and `numberReady` are both 2, the two pods are on two distinct nodes, and the control-plane taint is still present.

## Why shortcuts fail
Removing the taint changes cluster policy for every other workload and fails the guard.
