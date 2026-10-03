# Hints
1. Compare who the policy lets in (`describe networkpolicy`) with the labels of the actual client pods (`get pods --show-labels`).
2. NetworkPolicy evaluates traffic to the pod after the Service has translated the port. Which port does the container really listen on?
3. Patch `allow-clients` so its single ingress rule has `from.podSelector.matchLabels.role={{cl}}` and port `{{port}}`. Do not delete policies.
