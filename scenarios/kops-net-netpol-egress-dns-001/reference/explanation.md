# Egress policy without DNS

## Root cause
Once a pod is selected by an Egress policy, only the listed destinations are allowed. The policy allows TCP {{port}} to the app pods, but name resolution needs UDP/TCP 53 to CoreDNS
(pods in `kube-system`). Resolution fails ("bad address"), so the connection is never attempted.

## Approach
Add an egress rule to `kube-system` (select the namespace by its automatic label `kubernetes.io/metadata.name=kube-system`) on UDP and TCP 53, keeping the existing rule.

## What the verifier checks
From a client pod: `http://{{app}}/` returns the expected body (3 attempts); `http://{{other}}/` is blocked (2 attempts); the policy still exists.

## Why shortcuts fail
`egress: [{}]` or deleting the policy lets the client reach `{{other}}`.
