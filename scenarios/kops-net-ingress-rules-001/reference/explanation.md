# Ingress with two path rules

## Approach
`kubectl create ingress` builds the object from `--rule=host/path=service:port`. A path ending in `*` becomes `pathType: Prefix`; without it the rule is `Exact`.
`kubectl -n {{ns}} create ingress {{app}}-edge --class={{class}} --rule="{{host}}/api*={{app}}-api:80" --rule="{{host}}/*={{app}}-web:80"`.

## What the verifier checks
The object's fields only: class name, host, per-path backend service/port, pathType Prefix; Services unchanged. **No ingress controller exists on this backend, so routing behaviour is not tested** (see docs/scenario-backlog.md, PF-NET-007 behavioural variant).

## Why shortcuts fail
Exact pathTypes and swapped backends fail the field checks.
