# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get networkpolicy
kubectl -n {{ns}} describe networkpolicy allow-clients
kubectl -n {{ns}} get pods --show-labels
kubectl -n {{ns}} patch networkpolicy allow-clients --type merge -p '{"spec":{"ingress":[{"from":[{"podSelector":{"matchLabels":{"role":"{{cl}}"}}}],"ports":[{"protocol":"TCP","port":{{port}}}]}]}}'
