# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl get crd
kubectl api-resources --api-group={{grp}}.kops.example
kubectl -n {{ns}} get {{short}} -o custom-columns=NAME:.metadata.name,PHASE:.spec.phase
kubectl -n {{ns}} create configmap ext-inventory --from-literal=kind={{kind}} --from-literal=apiGroup={{grp}}.kops.example --from-literal=shortName={{short}} --from-literal=ready={{nready}}
