# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl -n {{ns}} get services
kubectl get ingressclass
kubectl -n {{ns}} create ingress {{app}}-edge --class={{class}} --rule="{{host}}/api*={{app}}-api:80" --rule="{{host}}/*={{app}}-web:80"
