One worker node is reserved for the `{{team}}` team: it carries the label `dedicated={{team}}` and a matching `NoSchedule` taint.
The `{{app}}` Deployment in namespace `{{ns}}` belongs to that team and must run (2 replicas) on that node and nowhere else,
but its pods are Pending.

Fix the Deployment. The node's taint must stay in place.
