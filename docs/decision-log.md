# KOPS Decision Log

This log records reviewer decisions on the architecture proposal ([00-architecture-proposal.md](00-architecture-proposal.md), table "Decisions requested from the reviewer"). Numbers refer to that table.

## 2026-09-28 — Review round 1 (decisions 1–5, backend)

| # | Decision | Outcome | Consequence |
|---|---|---|---|
| 1 | B1 (`kind-node`) counts as "system-level" for the vertical slice | **Approved** | S09 and S10 (and stretch S12) run on `kind-node`. The slice contains no `vm` scenarios. |
| 2 | B2 engine (Incus VMs / libvirt / LXD) | **Deferred.** Not needed now; B2 comes later. | Spike S-2 is not scheduled. The `vm` class stays in the schema and in the catalog, so the 5 vm-only families (PF-CLU-003/004/005/006, PF-NOD-004) remain visible. Coverage reports mark them "uncovered: backend deferred", not silently dropped. CKA-ARC-02 and CKA-ARC-05 have no runnable scenario until B2 exists. Nothing is installed or initialised on the host for B2; the existing LXD 5.0 snap stays untouched. |
| 3 | Gateway/Ingress controller for Backend A | **Approved:** a single controller that serves both Ingress and Gateway API, pinned | The concrete controller is chosen in spike S-1, including a license check before adoption. |
| 4 | CNI for A/B1 | **Approved:** decide after measuring in spike S-1 (kindnet if its NetworkPolicy enforcement is verified, otherwise Calico) | Spike S-1 must include a NetworkPolicy enforcement test (positive and negative probes). |
| 5 | Kubernetes version | **Approved:** pin **1.35** for benchmark v1 | kind node image `v1.35.x`, pinned by digest. Revisit when CNCF publishes the next curriculum. |

**Still open:** decisions 6–16 (verifier model, agent integration, runtime language, layout, license, quarantine scope, held-out split, id prefix, difficulty, partial-credit reporting, mapping ambiguities).

## 2026-10-01 — Review round 2 (exam-fidelity decisions)

| Topic | Outcome | Consequence |
|---|---|---|
| Documentation access during a trial | **Offline mirror of the permitted docs** (kubernetes.io docs pinned to the benchmark Kubernetes version, plus helm and Gateway API docs), served on the isolated network. Internet stays forbidden. | The workstation gets one allowed docs host. Page fetches appear in the trace. The mirror version is recorded in the environment fingerprint. |
| Context switching | **Simulated.** Each task states which context to use. A trial can carry several contexts, only one of them is the target. | Schema needs a `contexts` field. Verifier adds a guard that non-target clusters are unchanged (wrong-context mutation = guard failure). |
| Cluster state between problems | **Every trial gets a fresh, clean environment.** | Replaces the "reuse a cluster with namespace-per-trial" idea from the review draft. Namespace reuse stays a possible later optimisation only if the reset self-test proves it. |
| Scoring | Open. Proposal in design-review.md §K. | |
