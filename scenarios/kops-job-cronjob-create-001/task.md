In namespace `{{ns}}`, create a CronJob named `{{app}}` that:
- runs on the schedule `{{sched}}`,
- uses image `busybox:1.36.1` and prints the single line `{{marker}}`,
- never lets two runs overlap (a new run is skipped while the previous one is still running),
- keeps the last 2 successful Jobs and the last 1 failed Job.

Then trigger one run right away as a Job named `{{app}}-now`, created from the CronJob, and let it finish.
