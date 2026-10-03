The `{{app}}` Deployment in namespace `{{ns}}` needs three configuration changes:
- environment variable `MSG` set to `{{msg}}`,
- a CPU limit of `{{cpu}}` on its container,
- pods running as the existing ServiceAccount `{{sa}}`.

Each of these normally triggers its own rollout. Production must see **one** rollout only: the Deployment must end up with exactly one new revision
(revision 2), with all three changes in it, fully rolled out and not left paused.
