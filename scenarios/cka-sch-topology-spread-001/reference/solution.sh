# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl get nodes --show-labels
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/nodeSelector"},{"op":"add","path":"/spec/template/spec/topologySpreadConstraints","value":[{"maxSkew":1,"topologyKey":"rack","whenUnsatisfiable":"DoNotSchedule","labelSelector":{"matchLabels":{"app":"{{app}}"}}}]}]'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
