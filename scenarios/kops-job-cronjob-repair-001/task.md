The CronJob `{{app}}-report` in namespace `{{ns}}` produces a report line, but the Jobs it creates never finish.

1. Repair the CronJob itself so that its future runs work.
2. Prove it: trigger one run right now as a Job named `{{job}}`, created from the CronJob's template, and let it complete
   (its log must contain the report line).

Do not change the CronJob's schedule or concurrency policy.
