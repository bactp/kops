# Must FAIL: the Secret is projected under its key name, so the file is token, not token.txt.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"replace","path":"/spec/template/spec/volumes/0","value":{"name":"site","projected":{"sources":[{"configMap":{"name":"{{app}}-page"}},{"secret":{"name":"{{app}}-token"}}]}}}]'
