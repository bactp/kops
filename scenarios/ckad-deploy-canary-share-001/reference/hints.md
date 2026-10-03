# Hints
1. Which pods do the Service's endpoints actually contain? Compare the Service selector with the labels of both Deployments' pods.
2. Replica counts decide the split when one Service selects both tracks. Total 4 pods, one canary.
3. Remove `track` from the Service selector (JSON patch `remove`), then scale stable to 3 and canary to 1.
