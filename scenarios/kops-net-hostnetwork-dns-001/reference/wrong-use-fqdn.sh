# Must FAIL: a fully qualified cluster name still cannot be resolved by the node's resolver.
kubectl -n {{ns}} patch deployment client -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","command":["sh","-c","while true; do if wget -q -T 2 -O /dev/null http://{{svc}}.{{ns}}.svc.cluster.local/; then echo OK; else echo FAIL; fi; sleep 2; done"]}]}}}}'
