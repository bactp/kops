# Service with endpoints but no data path

## Root cause
kube-proxy programs the node's Service rules. Its DaemonSet was updated to an image tag that does not exist, so its pod is gone and not replaced (`ImagePullBackOff`).
Rules that existed before stay in place (old Services keep working), but a Service created afterwards never gets rules: DNS resolves, the ClusterIP times out.

## Approach
The pods and endpoints of `{{app}}` look fine, so look at the components that implement Services: `kubectl -n kube-system get pods` shows kube-proxy not running; `describe daemonset`/events show the pull failure.
`kubectl -n kube-system rollout undo daemonset/kube-proxy` returns to the previous template (the working image); `rollout status` waits. Setting the image back by hand also works.

## What the verifier checks
Three HTTP requests via the Service name return the app body; the kube-proxy DaemonSet has a ready pod and an image `kube-proxy:v1.35.x`; the DaemonSet and its ConfigMap are unchanged in UID/data.

## Why shortcuts fail
A restart re-applies the broken template; deleting the DaemonSet removes kube-proxy.
