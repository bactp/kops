# Hints
1. A PDB protects the pods its selector matches. What labels do the pods carry?
2. `kubectl create poddisruptionbudget --help` lists `--selector`, `--min-available` and `--max-unavailable`.
3. Selector `component={{app}}`, `--max-unavailable=1` (or `--min-available=3`). Check the PDB's status afterwards.
