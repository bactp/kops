The pod of Deployment `{{app}}` in namespace `{{ns}}` runs three containers and shows as not fully ready.
Diagnose which container is failing and with which exit code.

Record your findings in a ConfigMap named `{{app}}-findings` in the same namespace with two keys:
- `container`: the name of the failing container
- `exitCode`: its last exit code (digits only)

This is a diagnosis task: do not modify the Deployment.
