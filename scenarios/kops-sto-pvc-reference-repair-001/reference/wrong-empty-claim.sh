# Must FAIL: the pod starts on the other, empty claim, so the saved file is not served.
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"{{app}}-scratch"}}]}}}}'
