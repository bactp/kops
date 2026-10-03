# Must FAIL: the old default is demoted but nothing replaces it.
kubectl patch storageclass standard -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
