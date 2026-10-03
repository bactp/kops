# Hints
1. Look at the pods of the failing Jobs: what does the event say about the image?
2. The Job's pod template is copied from the CronJob, so fix the source, not the symptom.
3. After patching the CronJob image, `kubectl create job <name> --from=cronjob/<cronjob>` makes a run on demand; `kubectl wait` or `kubectl get job` tells you when it is complete.
