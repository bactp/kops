# Drain a node for maintenance

## Approach
`kubectl drain` cordons the node and evicts its pods. Two obstacles: the node runs DaemonSet pods (`--ignore-daemonsets` is required) and the app pods use an `emptyDir`
(`--delete-emptydir-data` acknowledges that local data is lost). `kubectl drain -l maintenance=scheduled --ignore-daemonsets --delete-emptydir-data` does it, and the Deployment recreates the pods on the other worker.

## What the verifier checks
Nodes labelled `maintenance=scheduled` have `spec.unschedulable=true`; 4 Running pods, none on that node; replicas still 4; no other node cordoned.

## Why shortcuts fail
`cordon` alone leaves pods on the node; scaling down trades availability for convenience and trips the replica guard.
