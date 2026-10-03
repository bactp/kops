# Which node has the highest CPU requests

## Approach
`kubectl describe node <name>` has an "Allocated resources" table; its CPU "Requests" line adds up the requests of every pod on the node (system pods add the same small amount to each node).
Compare the three workers; the one with a single 700m pod beats 3 x 200m and 2 x 250m. `kubectl label node <heavy> capacity=tight`.
(Setup assigns pools so the heavy one rotates with the seed: here it is `pool={{heavy}}`.)

## What the verifier checks
The node carrying `pool={{heavy}}` has `capacity=tight`; exactly one node has the label; all six filler pods still run and the `big` Deployment is unchanged.

## Why shortcuts fail
Counting pods points at the wrong node; labelling all workers violates "no other node".
