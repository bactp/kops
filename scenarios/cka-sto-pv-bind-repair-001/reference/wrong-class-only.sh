# Must FAIL: only the class is corrected; capacity and access mode still mismatch.
kubectl patch pv {{app}}-vol -p '{"spec":{"storageClassName":"{{sc}}"}}'
