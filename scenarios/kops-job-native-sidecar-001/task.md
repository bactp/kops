The CronJob `{{app}}` in namespace `{{ns}}` runs a main container named `main` and a log-shipping container named `shipper`
that has to stay up while `main` works. Jobs created from it never finish, because `shipper` never exits.

Fix the CronJob so that its Jobs complete once `main` is done, while `shipper` is still a sidecar that runs next to `main`
(do not just delete it). Then prove it: create a Job named `{{job}}` from the CronJob and let it complete.

Do not change the CronJob's schedule.
