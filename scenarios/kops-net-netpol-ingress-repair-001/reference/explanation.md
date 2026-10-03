# NetworkPolicy blocks the real clients

## Root cause
`allow-clients` admits pods labelled `role={{wrong}}` on TCP 80. The real clients are labelled `role={{cl}}`, and NetworkPolicy ports refer to the
destination *pod* port ({{port}}), not the Service port (80). Under the namespace default-deny nothing else is allowed, so the clients are blocked.

## Approach
`kubectl get pods --show-labels` shows the client labels; `describe networkpolicy` shows the rule; patch the policy's ingress rule with the right `podSelector` and port `{{port}}`.
A merge patch replaces the `ingress` list as a whole.

## What the verifier checks
From a `role={{cl}}` pod: five-attempt-free HTTP 200 with the expected body (3 attempts). From the `role=scanner` pod: all attempts blocked. The default-deny policy exists and its spec is unchanged.

## Why shortcuts fail
Deleting the policies or removing the source restriction lets the scanner through. Fixing only the label leaves port 80 closed to the real port.
