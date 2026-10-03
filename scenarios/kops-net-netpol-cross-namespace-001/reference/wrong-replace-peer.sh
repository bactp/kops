# Must FAIL: replacing the same-namespace peer with the partner breaks the pods of the app's own namespace.
kubectl -n {{ns}} patch networkpolicy allow-same-namespace --type json -p '[{"op":"replace","path":"/spec/ingress/0/from","value":[{"namespaceSelector":{"matchLabels":{"kubernetes.io/metadata.name":"{{ns}}-partner"}}}]}]'
