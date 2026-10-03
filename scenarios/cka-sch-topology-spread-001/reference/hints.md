# Hints
1. Two things must change in the pod template: the pin has to go, and something that actively enforces the spread has to come in.
2. The spread is expressed per topology domain (a node label key). `maxSkew` and `whenUnsatisfiable` decide how strict it is.
3. `topologySpreadConstraints` with `topologyKey: rack`, `maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule` and a `labelSelector` matching the app's pods; remove `nodeSelector`.
