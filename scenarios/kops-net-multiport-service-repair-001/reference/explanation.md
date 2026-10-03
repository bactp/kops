# Two-port Service, two defects

## Root cause
A numeric `targetPort` must be a port the process listens on; a *named* `targetPort` must match a `name` under the container's `ports`.
Port 80 asks for `web-http`, but the container declares `http`: no endpoint port resolves. Port 9090 maps to the http port number, so it returns the main page instead of the admin page.

## Approach
`kubectl get deployment -o jsonpath` (or `describe`) shows container ports `http` and `admin`; patch both Service ports (a merge patch replaces the `ports` list): `http -> http` and `admin -> admin` (or `{{port2}}`).

## What the verifier checks
Three requests each to `:80` (`main-ok`) and `:9090` (`admin-ok`); two ready endpoints on each container port; Service UID/ClusterIP and Deployment template unchanged.

## Why shortcuts fail
Fixing only one port leaves the other broken; re-creating the Service changes UID/ClusterIP.
