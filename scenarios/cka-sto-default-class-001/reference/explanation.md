# Switching the default StorageClass

## Approach
The default is the annotation `storageclass.kubernetes.io/is-default-class: "true"`. Remove it (or set it to "false") on `standard` and set it on `{{sc}}`:
two `kubectl patch storageclass` commands (or `kubectl annotate --overwrite`).

## What the verifier checks
`{{sc}}` is annotated true; exactly one class is default; `standard` is not default; both classes exist.

## Why shortcuts fail
Promoting without demoting leaves two defaults; demoting alone leaves none. (This scenario checks the objects only: creating a claim and watching it bind is not possible with single kubectl commands on this backend.)
