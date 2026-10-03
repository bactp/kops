# ExternalName alias

## Approach
An `ExternalName` Service has no selector or endpoints; cluster DNS answers its name with a CNAME to `spec.externalName`.
`kubectl -n {{ns}} create service externalname {{alias}} --external-name={{svc}}.{{ns}}-data.svc.cluster.local`.

## What the verifier checks
From a client pod in `{{ns}}`, three requests to `http://{{alias}}/` return the backend's body; the Service has type ExternalName with the backend's DNS name; backend objects unchanged.

## Why shortcuts fail
A ClusterIP lookalike resolves but never reaches the backend; a wrong target name does not resolve.
