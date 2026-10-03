# Must FAIL: removing the policies restores access for everyone, including the scanner.
kubectl -n {{ns}} delete networkpolicy --all
