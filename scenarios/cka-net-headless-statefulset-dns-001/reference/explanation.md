# Headless governing Service

## Root cause
A Service with a cluster IP load-balances behind one virtual IP; peers that need every member's address require a *headless* Service (`clusterIP: None`), whose DNS name returns one A record per ready pod.
`spec.clusterIP` is immutable, so the Service cannot be patched into a headless one.

## Approach
`kubectl delete service {{svc}}` then `kubectl create service clusterip {{svc}} --clusterip=None --tcp=80:{{port}}` (the generated selector `app={{svc}}` matches the pods). The per-pod names `{{svc}}-N.{{svc}}.{{ns}}.svc` keep resolving.

## What the verifier checks
`clusterIP: None`; `nslookup {{svc}}.{{ns}}.svc.cluster.local` from the probe pod returns two pod addresses (10.244.x.x, the default kind pod CIDR); per-pod names resolve; the StatefulSet is unchanged.

## Why shortcuts fail
A differently named headless Service does not change what `{{svc}}` returns; deleting the StatefulSet breaks the guard. (Observation recorded while authoring: CoreDNS answers per-pod names even for ClusterIP Services, so only the Service-name lookup distinguishes the two.)
