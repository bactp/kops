# Downward API volume

## Approach
Replace the `podinfo` volume's source: `emptyDir` -> `downwardAPI` with items `labels` (`fieldRef: metadata.labels`) and `namespace` (`fieldRef: metadata.namespace`).
Use a JSON patch `replace` on `/spec/template/spec/volumes/0`; a strategic merge would keep `emptyDir` and the API would reject two volume sources.

## What the verifier checks
`/labels` contains `app="{{app}}"`, `/namespace` equals `{{ns}}` (3 requests each), image and mount path unchanged.

## Why shortcuts fail
A merge patch is refused; leaving out one item leaves a 404.
