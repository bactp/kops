The pods of the `{{app}}` Deployment in namespace `{{ns}}` are all Pending. The application is meant to run only on the
worker node pool called `{{pool}}`.

Make all three replicas run, and make sure they only run on nodes of the `{{pool}}` pool.

Constraints:
- Do not change any node labels.
- Keep 3 replicas.
