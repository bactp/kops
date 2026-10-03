The worker node labelled `maintenance=scheduled` is about to be serviced. Prepare it:
- no new pods may be scheduled onto it,
- the pods currently running on it must be evicted (system DaemonSet pods may stay),
- the `{{app}}` Deployment in namespace `{{ns}}` must still have all of its replicas running, on the remaining nodes.

Do not scale the Deployment down and do not take any other node out of service.
