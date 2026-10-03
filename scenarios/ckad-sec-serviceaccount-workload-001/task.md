The `{{app}}` Deployment in namespace `{{ns}}` currently runs with the namespace's default ServiceAccount and gets an API token mounted
although it never talks to the Kubernetes API.

Create a ServiceAccount named `{{sa}}`, run the Deployment's pods as that account, and make sure
the pods do not get an API token mounted (set this on the pod template itself).

Constraint: keep the same Deployment, image and replica count.
