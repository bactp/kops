# Must FAIL: deleting the claim is forbidden; the Deployment is left without storage.
kubectl -n {{ns}} delete pvc {{app}}-claim
