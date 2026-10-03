# Must FAIL: without the trailing * the rules get pathType Exact instead of Prefix.
kubectl -n {{ns}} create ingress {{app}}-edge --class={{class}} --rule="{{host}}/api={{app}}-api:80" --rule="{{host}}/={{app}}-web:80"
