The DaemonSet `{{app}}` in namespace `{{ns}}` is a node-level agent that must run on every node of the cluster,
including the control-plane node. At the moment it is missing from the control plane.

Fix the DaemonSet so that it runs on all nodes. Do not change the node's taints.
