The StatefulSet `{{svc}}` in namespace `{{ns}}` runs two replicas (`{{svc}}-0`, `{{svc}}-1`) that are peers of each other.
Its peers must discover each other by DNS: resolving `{{svc}}.{{ns}}.svc.cluster.local` has to return the address of **each** pod
(one record per replica), not a single virtual IP. Today it returns one cluster IP.

Fix the Service so that this works, and keep the per-pod names `{{svc}}-0.{{svc}}...` and `{{svc}}-1.{{svc}}...` resolving.
The StatefulSet already names Service `{{svc}}` as its governing Service; do not modify or re-create the StatefulSet.
