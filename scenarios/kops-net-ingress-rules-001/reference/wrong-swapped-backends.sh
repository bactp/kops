# Must FAIL: the routes point at the wrong Services.
kubectl -n {{ns}} create ingress {{app}}-edge --class={{class}} --rule="{{host}}/api*={{app}}-web:80" --rule="{{host}}/*={{app}}-api:80"
