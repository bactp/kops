# Switch to the Recreate strategy

## Root cause
The Deployment uses `RollingUpdate` with `maxSurge: 1`, so during an update old and new pods coexist, which the app cannot tolerate.

## Approach
1. `kubectl -n {{ns}} get deployment {{app}} -o jsonpath='{.spec.strategy}'` shows the current block.
2. `kubectl patch deployment {{app}} --type merge -p '{"spec":{"strategy":{"type":"Recreate","rollingUpdate":null}}}'`.
   The `rollingUpdate: null` is essential: the API rejects `type: Recreate` while a `rollingUpdate` block is still present.
3. `kubectl set env deployment/{{app}} MSG={{ver}}` triggers the new rollout (any pod template change would).
4. `kubectl rollout status deployment/{{app}}`.

## What the verifier checks
`strategy.type == Recreate`, `strategy.rollingUpdate` absent, five HTTP requests return `{{ver}}`, rollout complete, UID and replicas unchanged.

## Why shortcuts fail
Changing the type only is refused by the API (so strategy stays RollingUpdate). Changing the strategy without rolling out the new version leaves banner `v1`.
