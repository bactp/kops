# Must FAIL: runAsNonRoot alone does not satisfy the restricted profile (seccomp, capabilities, escalation).
kubectl -n {{ns}} patch deployment {{app}} -p '{"spec":{"template":{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":10001}}}}}'
