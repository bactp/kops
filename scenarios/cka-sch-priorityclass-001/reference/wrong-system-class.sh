# Must FAIL: an existing system class is used instead of the requested one.
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"priorityClassName":"system-cluster-critical"}}}}'
