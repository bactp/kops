The four pods of the `{{app}}` Deployment in namespace `{{ns}}` all run in one rack because the Deployment is pinned to it
with a node selector. The worker nodes carry a `rack` label.

Remove the pinning and make the scheduler guarantee an even spread instead: the number of pods in any rack must never differ
by more than one, and a pod must stay unscheduled rather than break that rule.
Afterwards all four replicas must be running on both workers.
