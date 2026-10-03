Service `{{app}}` in namespace `{{ns}}` currently sends all traffic to the `{{app}}-stable` Deployment (4 replicas).
A new build is available in the `{{app}}-canary` Deployment, which is scaled to zero.

Start a canary: 4 pods in total must serve the Service, exactly one of them from the canary release (so about a quarter of requests reach it).

Constraint: do not delete either Deployment or the Service.
