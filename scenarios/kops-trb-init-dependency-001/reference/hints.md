# Hints
1. `Init:0/1` means the first init container has not finished. Read its logs: `kubectl logs <pod> -c <init-container>`.
2. It resolves and calls a name. What exists in the namespace that could answer, and what is missing in front of it?
3. Create a Service named `{{dep}}` for the backend Deployment on port {{dport}}: `kubectl expose deployment ... --name=... --port=...`.
