# Must FAIL: labelling every node with the wrong value lets pods schedule but breaks the node-label guard and the pool placement.
kubectl label nodes --all pool={{pool}}-v2 --overwrite
