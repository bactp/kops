# Must FAIL: the binding subject is fixed but the Role still targets the wrong API group, so nothing is allowed.
kubectl -n {{ns}} patch rolebinding {{app}}-deployer --type json -p '[{"op":"replace","path":"/subjects/0/namespace","value":"{{ns}}"}]'
