# Three different faults in one namespace

## Faults
1. `{{b}}`: image `busybox:1.36.9` does not exist: `ImagePullBackOff`. Fix: `kubectl set image deployment/{{b}} web=busybox:1.36.1`.
2. `{{c}}`: the command runs `httpd-static`, which is not in the image: crash loop (`exec: "httpd-static": not found`, visible in logs/events). Fix: patch the command back to `httpd`.
3. `{{d}}`: `nodeSelector: disktype=ssd` matches no node: `Pending` with `didn't match Pod's node affinity/selector`. Fix: remove the selector (labelling nodes is forbidden).
`{{a}}` is healthy and must not be touched.

## What the verifier checks
Rollout complete and three HTTP 200 responses with the right body for each of `{{b}}`, `{{c}}`, `{{d}}`; all four Deployments still at 2 replicas; `{{a}}` spec and UID unchanged; no node has a `disktype` label.

## Why shortcuts fail
Scale-to-zero and node relabelling are caught by the guards.
