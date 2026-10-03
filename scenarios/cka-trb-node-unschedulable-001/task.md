All four pods of the `{{app}}` Deployment in namespace `{{ns}}` are Pending: no node accepts them.
The two worker nodes were put on hold by someone and never released.

Find out what is holding each worker back and release them, so that the Deployment runs on the workers.

Constraints:
- Keep the control-plane node's taint.
- Do not modify the Deployment.
