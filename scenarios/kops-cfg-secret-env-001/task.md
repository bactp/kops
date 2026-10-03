The `{{app}}` application in namespace `{{ns}}` talks to a backend that requires the credentials
username `{{user}}` and password `{{pw}}`. It reads them from the environment variables `DB_USERNAME` and `DB_PASSWORD`,
and shows `auth-ok` at `http://{{app}}.{{ns}}.svc.cluster.local/` once they are right (`auth-denied` otherwise).

Store the credentials in a Secret with the keys `username` and `password`, and make the Deployment consume them from it.

Constraint: the password must not appear as a literal value in the Deployment.
