# Projected volume

## Approach
A `projected` volume merges several sources (ConfigMap, Secret, downward API, service account token) into one directory.
Replace the volume `site` with `projected.sources: [configMap {{app}}-page, secret {{app}}-token with items key token -> path token.txt]` using a JSON patch `replace` of `/spec/template/spec/volumes/0` (a merge patch would leave the old `configMap` source in place next to `projected`).

## What the verifier checks
`/index.html` returns `page-ok`, `/token.txt` returns the token, image and mount path unchanged.

## Why shortcuts fail
A second mount puts the Secret in another directory; projecting without `items` produces a file named `token`.
