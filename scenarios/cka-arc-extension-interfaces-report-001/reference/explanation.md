# CRI, CNI and CSI as seen through the API

## Approach
- CRI: `kubectl get nodes -o wide` has a CONTAINER-RUNTIME column (`containerd://<version>`); the same string is in `.status.nodeInfo.containerRuntimeVersion`.
- CNI: pod networking is provided by a DaemonSet in `kube-system`; on this cluster it is `kindnet` (`kubectl -n kube-system get daemonsets`).
- CSI/provisioning: `kubectl get storageclass` marks the default class and shows its provisioner (`rancher.io/local-path`).
- The kubelet version is in `kubectl get nodes` (VERSION column).
Record the four values with `kubectl create configmap cluster-interfaces --from-literal=...`.

## What the verifier checks
Each key equals the value read from the live objects (`value_from`): node info, the `app=kindnet` DaemonSet name, the `standard` StorageClass provisioner; the DaemonSet and StorageClass are unchanged.
With the pinned node image (kindest/node v1.35.8) the values are `containerd://2.3.4`, `kindnet`, `rancher.io/local-path` and `v1.35.8`; the reference solution uses these literals, so a node image bump requires re-running the selftest.
