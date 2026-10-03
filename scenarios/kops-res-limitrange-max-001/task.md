The `{{app}}` Deployment in namespace `{{ns}}` has no running pods: they are rejected by the namespace's admission policy.

Change the Deployment so that both replicas run, with explicit memory requests and limits that satisfy the policy.

Constraints:
- The namespace policy belongs to the platform team: do not modify or delete it.
- Keep 2 replicas.
