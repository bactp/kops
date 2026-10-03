# Must FAIL: replacing the claim with an emptyDir starts the pod but loses the saved data.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"replace","path":"/spec/template/spec/volumes/0","value":{"name":"data","emptyDir":{}}}]'
