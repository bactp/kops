# Must FAIL: restarting re-applies the same broken image, so kube-proxy still cannot start.
kubectl -n kube-system rollout restart daemonset/kube-proxy
