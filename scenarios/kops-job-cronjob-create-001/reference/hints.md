# Hints
1. `kubectl create cronjob --help` shows what can be set directly. Not every field has a flag.
2. Concurrency and history limits live in the CronJob spec; they can be added with a patch.
3. `kubectl create job <name> --from=cronjob/<cronjob>` starts a run on demand.
