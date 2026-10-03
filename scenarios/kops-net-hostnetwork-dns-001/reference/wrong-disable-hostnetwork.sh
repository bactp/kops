# Must FAIL: the calls work again, but the client no longer runs on the host network.
kubectl -n {{ns}} patch deployment client --type json -p '[{"op":"remove","path":"/spec/template/spec/hostNetwork"}]'
