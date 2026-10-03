# Hidden oracle. One kubectl command per line, replayed through the Tool Gateway.
kubectl get nodes --show-labels
kubectl describe node -l pool={{heavy}}
kubectl label node -l pool={{heavy}} capacity=tight
