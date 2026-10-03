# Roll back to a specific revision

## Root cause
Revision 3 of the Deployment points at `busybox:1.36.99`, a tag that does not exist, so its pods sit in `ErrImagePull`/`ImagePullBackOff`
and the rollout never completes. The old pods (revision 2) keep serving, which hides the problem from users but not from `rollout status`.
The trap: `kubectl rollout undo` without a revision goes back to revision 2, which is healthy but announces `{{color}}-2`, not the required `{{color}}-1`.

## Approach
1. `kubectl -n {{ns}} rollout status deployment/{{app}}` shows it is waiting; `get pods` shows the image pull failure.
2. `kubectl -n {{ns}} rollout history deployment/{{app}}` lists revisions 1-3.
3. `kubectl -n {{ns}} rollout history deployment/{{app}} --revision=N` shows the pod template (env `MSG`) for each revision; revision 1 has `MSG={{color}}-1`.
4. `kubectl -n {{ns}} rollout undo deployment/{{app}} --to-revision=1`, then `rollout status`.

## What the verifier checks
- Five consecutive HTTP requests through the Service DNS name return a body equal to `{{color}}-1` (so revision 2 is not accepted).
- The Deployment rollout is complete (updated = ready = replicas = 3).
- Guards: Deployment UID unchanged (no delete/re-create) and replicas still 3.

## Why shortcuts fail
- `rollout undo` alone lands on the wrong banner. `set image` alone repairs the image but keeps `MSG={{color}}-2`.
- Delete and re-create loses the history and the UID guard fails.
