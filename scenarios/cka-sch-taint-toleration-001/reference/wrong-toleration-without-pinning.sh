# Must FAIL: a toleration alone also admits the pods onto the other worker; they are no longer confined to the dedicated node.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/nodeSelector"},{"op":"add","path":"/spec/template/spec/tolerations","value":[{"key":"dedicated","operator":"Equal","value":"{{team}}","effect":"NoSchedule"}]}]'
