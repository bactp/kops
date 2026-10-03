# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods,endpoints,service
kubectl -n kube-system get pods
kubectl -n kube-system describe daemonset kube-proxy
kubectl -n kube-system rollout history daemonset/kube-proxy
kubectl -n kube-system rollout undo daemonset/kube-proxy
kubectl -n kube-system rollout status daemonset/kube-proxy --timeout=120s
