Namespace `{{ns}}` runs four independent applications, each as a Deployment with 2 replicas and a Service on port 80:
`{{a}}`, `{{b}}`, `{{c}}` and `{{d}}`. After a bad release some of them are not working.

Find every broken application and repair it so that all of them are fully available and answer HTTP requests on their Services.

Constraints:
- Keep all four Deployments at 2 replicas and do not delete any of them.
- Do not modify nodes.
- Do not touch an application that is already healthy.
