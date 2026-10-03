Service `{{app}}` in namespace `{{ns}}` is supposed to expose two things of the same application:
- port 80: the main page (body `main-ok`)
- port 9090: the admin page (body `admin-ok`)

Neither works from inside the cluster. Repair the Service so that both ports return their pages.

Constraints: keep the Service's name and ClusterIP (do not delete and re-create it) and do not change the Deployment.
