# Hints
1. Which pods does the Service send traffic to right now? Compare the Service selector with the labels on each Deployment's pods.
2. The new release is not running yet. Bring it up and wait for it to be ready before you redirect traffic.
3. Scale green to 3, wait for the rollout, then patch the Service selector's `track` label to `green`. Leave blue alone.
