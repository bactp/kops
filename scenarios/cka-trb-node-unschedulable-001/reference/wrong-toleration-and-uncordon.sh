# Must FAIL: tolerating the taint changes the Deployment instead of releasing the node, and the hold taint stays.
kubectl uncordon -l hold=cordon
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"tolerations":[{"key":"{{key}}","operator":"Exists","effect":"NoSchedule"}]}}}}'
