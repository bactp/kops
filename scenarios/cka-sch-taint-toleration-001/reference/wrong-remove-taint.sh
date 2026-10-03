# Must FAIL: pods start, but only because the reservation taint was removed.
kubectl taint nodes -l dedicated={{team}} dedicated-
