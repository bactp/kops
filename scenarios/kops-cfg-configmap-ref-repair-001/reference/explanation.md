# ConfigMap references that do not resolve

## Root cause
Two separate mistakes produce the same symptom (`CreateContainerConfigError`):
1. `SETTING` references key `LOG_LEVEL`, but the ConfigMap key is `log_level` (keys are case sensitive).
2. `MODE` references ConfigMap `{{app}}-setting`, which does not exist; the real one is `{{app}}-settings`.
The kubelet reports only the first problem per container, so fixing one reveals the other.

## Approach
`kubectl -n {{ns}} describe pod` (events: `couldn't find key LOG_LEVEL in ConfigMap` / `configmap "..-setting" not found`),
`kubectl get configmap` to see the real name and keys, then one strategic-merge patch that corrects both `valueFrom.configMapKeyRef` entries
(containers and env entries are merged by `name`), then `rollout status`.

## What the verifier checks
Five HTTP requests return `{{level}} {{mode}}`; rollout complete; ConfigMap data unchanged; neither env entry carries a literal `value`.

## Why shortcuts fail
`kubectl set env SETTING=... MODE=...` produces correct output but hard-codes the values (guard). Adding a `LOG_LEVEL` key alters the ConfigMap (guard) and does not repair the second reference.
