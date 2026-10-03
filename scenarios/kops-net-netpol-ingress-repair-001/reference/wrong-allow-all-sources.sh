# Must FAIL: opening the rule to every source lets the scanner in.
kubectl -n {{ns}} patch networkpolicy allow-clients --type merge -p '{"spec":{"ingress":[{"ports":[{"protocol":"TCP","port":{{port}}}]}]}}'
