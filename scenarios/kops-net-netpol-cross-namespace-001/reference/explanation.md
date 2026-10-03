# Admit one namespace

## Root cause
`allow-same-namespace` has a single peer, `podSelector: {}`, which matches pods of the policy's own namespace only. Pods of other namespaces match no peer, so default-deny drops them.

## Approach
Select the partner namespace with a `namespaceSelector`. Every namespace carries the automatic label `kubernetes.io/metadata.name=<name>`, and the partner namespace also has `team=partners`;
either works. Add the peer as an *additional* item of `from` (a JSON-patch `add` to `/spec/ingress/0/from/-`), so the existing peer stays.

## What the verifier checks
A client in `{{ns}}-partner` gets HTTP 200 (3 attempts); a client in `{{ns}}-other` is blocked; a client in `{{ns}}` still gets HTTP 200.

## Why shortcuts fail
`namespaceSelector: {}` or deleting the policies admits the other namespace. Replacing `from` breaks same-namespace access.
