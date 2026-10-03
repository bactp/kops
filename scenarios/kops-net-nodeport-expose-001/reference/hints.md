# Hints
1. `kubectl expose` creates a Service from a workload and copies the selector for you. Look at its `--type`, `--port`, `--target-port` and `--name` flags.
2. The container port is in the Deployment spec. A node port can be chosen when you create the Service, or changed later with a patch.
3. Run `kubectl expose deployment ... --type=NodePort ...`, then patch `/spec/ports/0/nodePort` to the requested value.
