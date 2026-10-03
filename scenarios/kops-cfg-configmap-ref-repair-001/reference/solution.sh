# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get pods
kubectl -n {{ns}} describe pods
kubectl -n {{ns}} get configmap
kubectl -n {{ns}} get configmap {{app}}-settings -o yaml
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","env":[{"name":"SETTING","valueFrom":{"configMapKeyRef":{"name":"{{app}}-settings","key":"log_level"}}},{"name":"MODE","valueFrom":{"configMapKeyRef":{"name":"{{app}}-settings","key":"mode"}}}]}]}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
