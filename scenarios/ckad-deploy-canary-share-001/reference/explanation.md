# Canary by replica ratio

## Approach
A Service balances over every ready pod its selector matches. The Service selects `track=stable`, which excludes the canary. Remove the `track` key (keep `app`) so both Deployments' pods match, then set replicas to 3 stable + 1 canary.
`kubectl scale` both Deployments and `kubectl patch service ... --type json -p '[{"op":"remove","path":"/spec/selector/track"}]'`.

## What the verifier checks
Four ready endpoints on the container port; exactly one ready canary pod and three ready stable pods; the Service selector has no `track` key; UIDs of all three objects unchanged.

## Why shortcuts fail
Scaling without opening the selector leaves the canary unreachable; opening the selector without scaling gives no canary pod; a full switch is not a canary.
