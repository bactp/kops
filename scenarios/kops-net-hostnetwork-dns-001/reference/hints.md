# Hints
1. Compare this pod with an ordinary pod. Which network does it use, and which DNS server does it therefore ask?
2. There is a `dnsPolicy` value made for pods that use the host network and still need cluster DNS.
3. Patch the pod template with `dnsPolicy: ClusterFirstWithHostNet` and wait for the new pod.
