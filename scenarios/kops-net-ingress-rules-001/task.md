Namespace `{{ns}}` has two Services: `{{app}}-api` and `{{app}}-web` (both on port 80), and an IngressClass named `{{class}}`.

Create an Ingress named `{{app}}-edge` in `{{ns}}` that uses class `{{class}}` and publishes host `{{host}}`:
- path `/api` (pathType `Prefix`) goes to Service `{{app}}-api`, port 80
- path `/` (pathType `Prefix`) goes to Service `{{app}}-web`, port 80

Do not modify the Services.
