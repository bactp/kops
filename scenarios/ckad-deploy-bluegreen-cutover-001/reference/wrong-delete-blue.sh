# Must FAIL: green is promoted but blue is removed, so rollback is impossible.
kubectl -n {{ns}} scale deployment/{{app}}-green --replicas=3
kubectl -n {{ns}} rollout status deployment/{{app}}-green --timeout=120s
kubectl -n {{ns}} patch service {{app}} -p '{"spec":{"selector":{"app":"{{app}}","track":"green"}}}'
kubectl -n {{ns}} delete deployment {{app}}-blue
