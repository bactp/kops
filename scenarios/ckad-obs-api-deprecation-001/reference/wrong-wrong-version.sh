# Must FAIL: autoscaling/v2beta2 is replaced by autoscaling/v1, which is served but is not the stable v2 the manifest needs (and the other manifests are untouched).
kubectl -n {{ns}} patch configmap release-manifests --type merge -p '{"data":{"hpa.yaml":"apiVersion: autoscaling/v1\nkind: HorizontalPodAutoscaler\nmetadata: {name: web, namespace: {{ns}}}\n"}}'
