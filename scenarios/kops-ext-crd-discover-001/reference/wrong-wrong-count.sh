# Must FAIL: the ready count is off by one (counting all objects instead of Ready ones).
kubectl -n {{ns}} create configmap ext-inventory --from-literal=kind={{kind}} --from-literal=apiGroup={{grp}}.kops.example --from-literal=shortName={{short}} --from-literal=ready=4
