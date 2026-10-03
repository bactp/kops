# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get deployment {{app}} -o yaml
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":{{uid}}},"containers":[{"name":"web","securityContext":{"readOnlyRootFilesystem":true,"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}},"volumeMounts":[{"name":"scratch","mountPath":"/tmp"}]}],"volumes":[{"name":"scratch","emptyDir":{}}]}}}}'
kubectl -n {{ns}} rollout status deployment/{{app}} --timeout=120s
