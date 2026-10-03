# Must FAIL: deleting the StatefulSet violates the guard.
kubectl -n {{ns}} delete statefulset {{svc}}
