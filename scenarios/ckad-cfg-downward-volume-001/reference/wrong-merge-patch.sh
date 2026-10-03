# Must FAIL: a merge patch leaves the emptyDir source in place next to downwardAPI, which the API rejects, so nothing changes.
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"volumes":[{"name":"podinfo","downwardAPI":{"items":[{"path":"labels","fieldRef":{"fieldPath":"metadata.labels"}},{"path":"namespace","fieldRef":{"fieldPath":"metadata.namespace"}}]}}]}}}}'
