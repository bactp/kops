# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl get nodes -o wide
kubectl -n kube-system get daemonsets
kubectl get storageclass
kubectl create configmap cluster-interfaces -n {{ns}} --from-literal=runtime=containerd://2.3.4 --from-literal=cni=kindnet --from-literal=provisioner=rancher.io/local-path --from-literal=kubelet=v1.35.8
