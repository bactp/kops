# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get networkpolicy
kubectl -n {{ns}} describe networkpolicy allow-same-namespace
kubectl get namespaces --show-labels
kubectl -n {{ns}} patch networkpolicy allow-same-namespace --type json -p '[{"op":"add","path":"/spec/ingress/0/from/-","value":{"namespaceSelector":{"matchLabels":{"kubernetes.io/metadata.name":"{{ns}}-partner"}}}}]'
