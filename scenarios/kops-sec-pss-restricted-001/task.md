Namespace `{{ns}}` enforces the Pod Security `restricted` profile. The `{{app}}` Deployment in it has no running pods
because the pods are rejected when the ReplicaSet tries to create them.

Make the Deployment comply with the policy so that both replicas run, ready, and Service `{{app}}` (port 80) answers.

Constraint: do not change the namespace's Pod Security labels.
