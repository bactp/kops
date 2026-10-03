# One rollout for several changes

## Approach
`kubectl rollout pause deployment/{{app}}` stops the controller from reacting to template changes; make all edits (`set env`, `set resources`, `set serviceaccount`), then `kubectl rollout resume`.
The controller creates one new ReplicaSet for the final template: revision 2.

## What the verifier checks
The three template values, annotation `deployment.kubernetes.io/revision == "2"`, `spec.paused` not true and a complete rollout.

## Why shortcuts fail
Without pausing, every `set` command starts a rollout (revision 4). Pausing without resuming applies nothing.
