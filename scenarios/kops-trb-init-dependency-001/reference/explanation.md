# Init container waiting for a Service

## Approach
`kubectl get pods` shows `Init:0/1`; the init container's logs say `waiting for {{dep}}:{{dport}}`. The namespace contains Deployment `{{dep}}-server` but no Service called `{{dep}}`.
`kubectl expose deployment {{dep}}-server --name={{dep}} --port={{dport}}` creates it with the right selector; the init container then succeeds.

## What the verifier checks
Rollout complete with two Running pods; Service `{{dep}}` has a ready endpoint on {{dport}}; the init container spec and the backend Deployment are unchanged.

## Why shortcuts fail
Removing the init container trips the guard. `kubectl create service clusterip {{dep}}` selects `app={{dep}}`, which no pod carries, so there are no endpoints and the gate keeps waiting.
