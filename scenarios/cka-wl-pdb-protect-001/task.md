The `{{app}}` Deployment in namespace `{{ns}}` runs 4 replicas. During node maintenance at most one of its pods may be
voluntarily evicted at a time, and the others must stay available.

Create a PodDisruptionBudget named `{{app}}-pdb` that enforces this for all four pods.
Do not modify the Deployment.
