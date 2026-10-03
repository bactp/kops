# Host network and cluster DNS

## Root cause
A pod with `hostNetwork: true` uses the node's network namespace and, with the default `dnsPolicy: ClusterFirst`, **falls back to the node's resolver**, not CoreDNS. Cluster names (short or fully qualified) do not resolve (`wget: bad address`).

## Approach
`kubectl logs deployment/client` shows `FAIL`; the pod spec shows `hostNetwork: true`. Set `dnsPolicy: ClusterFirstWithHostNet` so the pod still sits on the host network but resolves names through cluster DNS.

## What the verifier checks
The last three log lines of the client pod(s) have at least two `OK` and no `FAIL`; the pod template still has `hostNetwork: true`; the backend is unchanged.

## Why shortcuts fail
Turning hostNetwork off breaks the requirement; an FQDN does not help without cluster DNS.
