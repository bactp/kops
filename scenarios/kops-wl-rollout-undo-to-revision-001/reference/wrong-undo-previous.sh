# Must FAIL: plain `rollout undo` goes to revision 2, which is healthy but serves the wrong banner.
kubectl -n {{ns}} rollout undo deployment/{{app}}
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
