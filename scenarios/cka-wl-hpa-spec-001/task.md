Configure autoscaling for the `{{app}}` Deployment in namespace `{{ns}}`:
- a HorizontalPodAutoscaler named `{{app}}` targeting the Deployment,
- at least {{min}} and at most {{max}} replicas,
- scale on average CPU utilisation of {{cpu}} %.

CPU-utilisation autoscaling only works if the pods declare how much CPU they request. Make the Deployment eligible as well.
(This cluster has no metrics pipeline, so do not expect the HPA to report a current value.)
