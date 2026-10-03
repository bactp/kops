The pods of the `{{app}}` Deployment in namespace `{{ns}}` keep restarting and are never stable.
Find out why and fix it so that both replicas become ready and stay up.

Constraints:
- The container must keep a memory limit, and the limit must not be larger than `{{cap}}`.
- Keep 2 replicas.
