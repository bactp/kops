# Hints
1. The update behaviour of a Deployment lives under `.spec.strategy`. Look at what is configured now.
2. `Recreate` has no tuning knobs. If you only change the type, the API server will complain about the leftover block.
3. Use a merge patch that sets `type` to `Recreate` and `rollingUpdate` to `null`, then change the `MSG` environment variable (`kubectl set env`) to roll out the new release.
