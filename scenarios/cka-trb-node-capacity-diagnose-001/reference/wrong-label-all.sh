# Must FAIL: every worker labelled; only one may carry the label.
kubectl label nodes -l '!node-role.kubernetes.io/control-plane' capacity=tight
