# Hints
1. `kubectl autoscale --help` has flags for minimum, maximum and the CPU percentage.
2. Utilisation is measured relative to something the pod declares. Does this container declare it?
3. `kubectl set resources deployment/<name> --requests=cpu=<value>` and then `kubectl autoscale deployment <name> --min=... --max=... --cpu-percent=...`.
