# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get role {{app}}-deployer -o yaml
kubectl -n {{ns}} get rolebinding {{app}}-deployer -o yaml
kubectl -n {{ns}} patch role {{app}}-deployer --type json -p '[{"op":"replace","path":"/rules/0/apiGroups","value":["apps"]},{"op":"replace","path":"/rules/1/apiGroups","value":["apps"]}]'
kubectl -n {{ns}} patch rolebinding {{app}}-deployer --type json -p '[{"op":"replace","path":"/subjects/0/namespace","value":"{{ns}}"}]'
