# NodePort exposure

## Approach
`kubectl -n {{ns}} expose deployment {{app}} --name={{app}}-public --type=NodePort --port=80 --target-port={{port}}` copies the Deployment's selector; the node port is allocated randomly,
so pin it: `kubectl patch service {{app}}-public --type json -p '[{"op":"replace","path":"/spec/ports/0/nodePort","value":{{np}}}]'`.
(`kubectl create service nodeport {{app}}-public --tcp=80:{{port}} --node-port={{np}}` also sets the port, but its selector would be `app={{app}}-public`; it would need a selector patch to get endpoints.)

## What the verifier checks
Type NodePort, port 80, targetPort {{port}}, nodePort {{np}}; two ready endpoints on {{port}}; HTTP 200 with the expected body through the Service DNS name; Deployment template unchanged.

## Why shortcuts fail
A ClusterIP Service fails the type check; a random nodePort fails the nodePort check.
