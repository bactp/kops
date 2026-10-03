# Must FAIL: the class exists but the pods still run with priority 0.
kubectl create priorityclass {{pc}} --value={{val}} --description="critical workloads"
