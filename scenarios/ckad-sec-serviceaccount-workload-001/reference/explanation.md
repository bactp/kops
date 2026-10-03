# Dedicated ServiceAccount, no token

## Approach
1. `kubectl -n {{ns}} create serviceaccount {{sa}}`
2. `kubectl -n {{ns}} set serviceaccount deployment/{{app}} {{sa}}`
3. `kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"automountServiceAccountToken":false}}}}'`
4. `rollout status`.

## What the verifier checks
Template `serviceAccountName` equals `{{sa}}`, the account exists, running pods use it, template `automountServiceAccountToken` is `false`, rollout complete, UID/replicas/image unchanged.

## Why shortcuts fail
Doing only one half leaves either the default identity or the mounted token.
