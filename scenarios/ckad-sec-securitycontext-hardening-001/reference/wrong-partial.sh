# Must FAIL: only the user is changed; filesystem, escalation and capabilities remain open.
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":{{uid}}}}}}}'
