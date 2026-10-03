# Must FAIL: without policies every namespace can connect.
kubectl -n {{ns}} delete networkpolicy --all
