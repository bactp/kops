# Hints
1. Which node carries the label? Which pods run on it (`get pods -o wide`)?
2. `kubectl drain` does both jobs (stop scheduling, evict). If it refuses, read the message: it names the flags it needs.
3. `kubectl drain <node-or-selector> --ignore-daemonsets --delete-emptydir-data`, then wait for the Deployment to be fully available again.
