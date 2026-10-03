The pods of the `{{app}}` Deployment in namespace `{{ns}}` are stuck in an `Init` state and never start.
Find out what they are waiting for and provide it, so both replicas become Ready.

Constraints:
- Do not remove or modify the init container.
- Do not modify the backend Deployment that already exists in the namespace.
