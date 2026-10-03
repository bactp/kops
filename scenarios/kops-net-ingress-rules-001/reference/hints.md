# Hints
1. `kubectl create ingress --help` documents the `--rule` format and the `--class` flag.
2. By default a rule's pathType is `Exact`. The help text shows how to ask for `Prefix`.
3. Two rules: `{{host}}/api*={{app}}-api:80` and `{{host}}/*={{app}}-web:80`, plus `--class={{class}}`.
