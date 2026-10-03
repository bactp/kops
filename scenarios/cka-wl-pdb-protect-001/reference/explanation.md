# PodDisruptionBudget

## Approach
Read the real pod labels (`get pods --show-labels` shows `component={{app}}`, there is no `app` label), then
`kubectl -n {{ns}} create poddisruptionbudget {{app}}-pdb --selector=component={{app}} --max-unavailable=1` (equivalently `--min-available=3`).

## What the verifier checks
The PDB status reports 4 expected pods and `disruptionsAllowed == 1` (this is what the eviction API will actually enforce); the Deployment is unchanged.

## Why shortcuts fail
A selector that matches nothing reports `expectedPods: 0`. `minAvailable=4` yields `disruptionsAllowed: 0`.
