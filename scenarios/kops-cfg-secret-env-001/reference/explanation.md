# Create a Secret and consume it

## Approach
1. `kubectl -n {{ns}} create secret generic {{app}}-db --from-literal=username={{user}} --from-literal=password={{pw}}`
2. `kubectl -n {{ns}} set env deployment/{{app}} --from=secret/{{app}}-db --prefix=DB_` maps each Secret key to an env var named `DB_` + upper-cased key, i.e. `DB_USERNAME` and `DB_PASSWORD`, using `secretKeyRef` under the hood.
3. Wait for the rollout; the page flips from `auth-denied` to `auth-ok`.
(A `patch` with explicit `secretKeyRef` entries is equally valid.)

## What the verifier checks
HTTP body is `auth-ok`; a Secret in the namespace has a `password` key; no env entry for `DB_PASSWORD`/`DB_USERNAME` carries a literal `value`.

## Why shortcuts fail
`set env DB_PASSWORD=...` makes the page say auth-ok but fails the no-literal guard. A Secret without wiring leaves auth-denied.
