Namespace `{{ns}}` holds filler workloads that were spread by hand over the three worker nodes.
Capacity planning needs to know which worker node currently has the highest total CPU **requests** committed by the pods of `{{ns}}`
(compare requests, not usage, and not the number of pods).

Label that one node `capacity=tight`. No other node may carry that label.
Do not modify the workloads.
