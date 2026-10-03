The pods of the `{{app}}` Deployment in namespace `{{ns}}` restart over and over and never become Ready.
The application is fine, it just needs about {{delay}} seconds before it starts listening.

Fix the Deployment so that both replicas become Ready and stay up without restarts.

Constraints:
- Keep a liveness probe on `/healthz`: a hung application must still be restarted after start-up.
- Keep 2 replicas.
