# Must FAIL: an empty namespaceSelector admits every namespace, including the blocked one.
kubectl -n {{ns}} patch networkpolicy allow-same-namespace --type json -p '[{"op":"add","path":"/spec/ingress/0/from/-","value":{"namespaceSelector":{}}}]'
