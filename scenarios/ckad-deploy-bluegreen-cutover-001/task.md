Application `{{app}}` in namespace `{{ns}}` is served from two Deployments: `{{app}}-blue` (live) and `{{app}}-green`
(the new release, currently scaled to zero). Clients always call Service `{{app}}` on port 80.

Switch production to the green release: it must run 3 ready pods, and the Service must send clients to it.

Constraints:
- Keep `{{app}}-blue` deployed with 3 replicas so that you can roll back quickly.
- Do not delete and re-create the Service.
