# Must FAIL: literal values satisfy the page but violate the no-literals guard.
kubectl -n {{ns}} set env deployment/{{app}} SETTING={{level}} MODE={{mode}}
