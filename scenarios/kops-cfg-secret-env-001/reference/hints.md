# Hints
1. First create the Secret; `kubectl create secret generic --help` shows how to give it keys.
2. `kubectl set env` can take its values from a Secret instead of literals, and can add a prefix to the variable names.
3. Secret keys are `username` and `password`; with `--from=secret/<name> --prefix=DB_` the variables become `DB_USERNAME` and `DB_PASSWORD`.
