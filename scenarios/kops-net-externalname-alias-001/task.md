The application in namespace `{{ns}}` needs to call the `{{svc}}` service that lives in namespace `{{ns}}-data`,
but should use a local name for it: pods in `{{ns}}` must be able to open `http://{{alias}}/`.

Provide that name by creating a Service called `{{alias}}` in `{{ns}}` that maps to the backend through DNS
(do not create copies of the backend's pods or endpoints). Do not change anything in `{{ns}}-data`.
