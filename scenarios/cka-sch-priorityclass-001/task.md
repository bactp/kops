The `{{app}}` Deployment in namespace `{{ns}}` is business critical and should be favoured by the scheduler over ordinary workloads.

Create a PriorityClass named `{{pc}}` with value `{{val}}` and make the pods of the Deployment use it.
The class must not become the default priority for other pods in the cluster.
