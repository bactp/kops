# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n kube-system get pods
kubectl -n kube-system get service kube-dns -o yaml
kubectl -n kube-system get endpoints kube-dns
kubectl -n kube-system get pods --show-labels
kubectl -n kube-system patch service kube-dns --type merge -p '{"spec":{"selector":{"k8s-app":"kube-dns"}}}'
kubectl -n kube-system get configmap coredns -o yaml
kubectl -n kube-system patch configmap coredns --type merge -p '{"data":{"Corefile":".:53 {\n    errors\n    health {\n       lameduck 5s\n    }\n    ready\n    kubernetes cluster.local in-addr.arpa ip6.arpa {\n       pods insecure\n       fallthrough in-addr.arpa ip6.arpa\n       ttl 30\n    }\n    prometheus :9153\n    forward . /etc/resolv.conf {\n       max_concurrent 1000\n    }\n    cache 30\n    loop\n    reload\n    loadbalance\n}\n"}}'
kubectl -n kube-system rollout restart deployment/coredns
kubectl -n kube-system rollout status deployment/coredns --timeout=120s
