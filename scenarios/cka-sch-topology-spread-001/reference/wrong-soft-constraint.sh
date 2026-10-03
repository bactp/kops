# Must FAIL: ScheduleAnyway is only a preference, not the required guarantee.
kubectl -n {{ns}} patch deployment {{app}} --type json -p '[{"op":"remove","path":"/spec/template/spec/nodeSelector"},{"op":"add","path":"/spec/template/spec/topologySpreadConstraints","value":[{"maxSkew":1,"topologyKey":"rack","whenUnsatisfiable":"ScheduleAnyway","labelSelector":{"matchLabels":{"app":"{{app}}"}}}]}]'
