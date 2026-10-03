# Must FAIL: token mount is disabled but the pods still run as the default account.
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"automountServiceAccountToken":false}}}}'
