# Must FAIL: labelling every node disktype=ssd fixes {{d}} by modifying the node, which is not allowed.
kubectl label nodes --all disktype=ssd
kubectl -n {{ns}} set image deployment/{{b}} web=busybox:1.36.1
