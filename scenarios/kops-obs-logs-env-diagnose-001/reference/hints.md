# Hints
1. What does the container print before it exits? `kubectl logs` (and `--previous` for a crashed container) will tell you.
2. The message names a variable. What kind of value does the application expect for it? Look at what else lives in the namespace.
3. Set `CACHE_HOST` to the name of the cache Service with `kubectl set env`. If the log message changes, read it again.
