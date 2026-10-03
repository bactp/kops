# Must FAIL: deleting and re-creating the Deployment loses history (UID guard) and does not serve the required banner.
kubectl -n {{ns}} delete deployment {{app}}
kubectl -n {{ns}} create deployment {{app}} --image=busybox:1.36.1 --replicas=3
