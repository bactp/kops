# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} describe networkpolicy client-egress
kubectl -n {{ns}} patch networkpolicy client-egress --type json -p '[{"op":"add","path":"/spec/egress/-","value":{"to":[{"namespaceSelector":{"matchLabels":{"kubernetes.io/metadata.name":"kube-system"}}}],"ports":[{"protocol":"UDP","port":53},{"protocol":"TCP","port":53}]}}]'
