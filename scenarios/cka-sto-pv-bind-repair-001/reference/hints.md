# Hints
1. `kubectl describe pvc` explains why nothing binds. Then compare the claim with the volume attribute by attribute.
2. Binding needs a matching storage class, enough capacity and compatible access modes. The claim is fixed, so the volume must change.
3. `kubectl patch pv {{app}}-vol` with `spec.storageClassName`, `spec.accessModes` and `spec.capacity.storage` matching the claim.
