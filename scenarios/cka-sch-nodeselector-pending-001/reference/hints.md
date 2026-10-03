# Hints
1. The scheduler tells you why it cannot place the pods: look at the pod events.
2. Compare the selector in the pod template with the labels that the nodes really carry.
3. Patch `spec.template.spec.nodeSelector` so that `pool` equals `{{pool}}`; do not touch the nodes.
