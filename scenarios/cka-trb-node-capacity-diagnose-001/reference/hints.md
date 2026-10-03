# Hints
1. `kubectl describe node` summarises what is allocated on a node. Which part of that summary is about requests?
2. Do not count pods; add up requested CPU. System pods add the same amount to every node, so they do not change the ranking.
3. Compare the three worker nodes' CPU request totals, then `kubectl label node <that-node> capacity=tight`.
