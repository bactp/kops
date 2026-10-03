# Forbidden because of a wrong API group and a wrong subject namespace

## Root cause
1. The Role lists `deployments` under `apiGroups: [""]` (the core group). Deployments are in the `apps` group, so no rule matches.
2. The RoleBinding subject points at ServiceAccount `{{sa}}` in namespace `default`, not `{{ns}}`, so it does not bind the real account.

## Approach
Use `kubectl auth can-i <verb> deployments.apps --as=system:serviceaccount:{{ns}}:{{sa}}` to reproduce; inspect Role and RoleBinding with `get -o yaml`;
patch rules[0] and rules[1] `apiGroups` to `["apps"]`, and patch the subject's `namespace` to `{{ns}}`.

## What the verifier checks
can-i allows get/list/patch deployments and update deployments/scale in `{{ns}}`; denies delete deployments, get secrets, patch deployments in kube-system, create pods.

## Why shortcuts fail
cluster-admin fails the deny checks. Fixing only the subject or only the rules leaves the allow checks failing.
