# Must FAIL: both classes end up marked default, which is ambiguous.
kubectl patch storageclass {{sc}} -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
