The landing page of the `{{app}}` application (namespace `{{ns}}`) is built from a ConfigMap. It currently says `{{old}}`.

Change the page so that clients of Service `{{app}}` on port 80 get exactly `{{new}}` (a single line), and make sure
the running application is actually serving it, not just that the stored configuration was edited.

Constraint: keep using the existing ConfigMap; do not delete it.
