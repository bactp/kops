# Short Service names do not cross namespaces

## Root cause
Pods resolve `{{svc}}` through the search path `<ns>.svc.cluster.local`, so a bare name only finds Services in the pod's own namespace.
The backend is in `{{ns}}-backend`; the client needs `{{svc}}.{{ns}}-backend` (or the full `...svc.cluster.local`) name.

## Approach
Read the client logs (`FAIL`), find where `{{svc}}` lives (`kubectl get svc -A`), then point `TARGET` at `http://{{svc}}.{{ns}}-backend.svc.cluster.local/` with `kubectl set env`, and wait for the rollout.
An ExternalName Service named `{{svc}}` in the client namespace that points at the backend FQDN would also work (the guard only rejects local ClusterIP Services).

## What the verifier checks
The last three log lines of the client pod(s) contain at least two `OK` and no `FAIL`; backend Deployment and Service unchanged; no ClusterIP Service exists in the client namespace.

## Why shortcuts fail
A local ClusterIP Service named `{{svc}}` has no endpoints, so calls still fail. Pointing at the wrong namespace keeps failing.
