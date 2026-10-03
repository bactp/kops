# Hints
1. Resolve the Service name from a pod today: what do you get back, and what would the peers need instead?
2. A Service that returns its pods' addresses directly has no cluster IP. Can an existing Service's `clusterIP` be changed?
3. Delete and re-create the same-named Service with `--clusterip=None` (`kubectl create service clusterip ... --clusterip=None --tcp=80:<port>`).
