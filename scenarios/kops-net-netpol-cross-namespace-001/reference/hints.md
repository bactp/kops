# Hints
1. Which peers does the existing ingress rule list? What does a `podSelector` without a namespace selector match?
2. NetworkPolicy peers can select namespaces by label. `kubectl get namespaces --show-labels` shows what is available, including an automatic name label.
3. Append a peer with `namespaceSelector.matchLabels` for the partner namespace to the existing `from` list (do not replace the list).
