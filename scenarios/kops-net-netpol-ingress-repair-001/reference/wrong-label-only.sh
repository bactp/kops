# Must FAIL: the source label is fixed but the policy still opens port 80 instead of the container port.
kubectl -n {{ns}} patch networkpolicy allow-clients --type merge -p '{"spec":{"ingress":[{"from":[{"podSelector":{"matchLabels":{"role":"{{cl}}"}}}],"ports":[{"protocol":"TCP","port":80}]}]}}'
