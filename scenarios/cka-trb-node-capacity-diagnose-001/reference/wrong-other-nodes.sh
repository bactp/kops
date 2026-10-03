# Must FAIL: labelling the other workers (the ones with more pods but less requested CPU) is the pod-count mistake.
kubectl label node -l pool,pool!={{heavy}} capacity=tight
