# Two holds on the workers

## Root cause
Worker 1 is cordoned (`spec.unschedulable: true`, shown as `SchedulingDisabled`). Worker 2 has a custom `NoSchedule` taint. The control plane is tainted by default. Together no node accepts the pods.

## Approach
`kubectl get nodes` shows `SchedulingDisabled`; `kubectl describe node` lists the taint. `kubectl uncordon <node>` and `kubectl taint nodes <node> {{key}}-` (trailing `-` removes the taint) release them.

## What the verifier checks
No labelled worker is unschedulable, the hold taint is gone, 4 Running pods on the workers, the control-plane taint still present, and the Deployment unchanged.

## Why shortcuts fail
A toleration modifies the workload and leaves worker 1 cordoned and the taint in place; removing the control-plane taint trips the guard.
