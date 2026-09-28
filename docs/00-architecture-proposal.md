# KOPS Track A2 — Architecture Proposal (Phases 1–7)

**W1-KOPS · Track A2: CKA/CKAD Execution & Evaluation Environment**

- **Date:** 2026-09-26
- **Status:** **FOR REVIEW. No runtime or scenario implementation has been started** (brief §18).
- **Scope:** an executable, deterministic benchmark for Kubernetes AI agents, grounded in the public CKA/CKAD competency specifications. It is *not* an exam-prep product.

**Research question it must serve:**

> Same scenarios, environment, tools, verifier and budgets: what operational competency does Kubernetes specialisation of a model actually add, and where does it still fail relative to the CKA/CKAD-aligned competency space?

---

## Document map

| Part | Deliverable | Files |
|---|---|---|
| A | Repository inventory | [reference-inventory.md](reference-inventory.md), [reference-inventory.csv](reference-inventory.csv) |
| B | Cross-repository architecture comparison | [cross-repo-architecture-comparison.md](cross-repo-architecture-comparison.md), [references/](references/) (7 notes: 5 P0 + ckad-2026/ckad-dojo split + P1 combined) |
| C | Problem-family catalog | [problem-family-catalog.yaml](problem-family-catalog.yaml), [competency-model.yaml](competency-model.yaml), [cka-ckad-coverage-matrix.md](cka-ckad-coverage-matrix.md) |
| D | Coverage-gap matrix | [coverage-gap-analysis.md](coverage-gap-analysis.md), [cka-ckad-coverage-matrix.md](cka-ckad-coverage-matrix.md) |
| E | License / contamination risk matrix | [license-contamination-risk.md](license-contamination-risk.md), [contamination-denylist.yaml](contamination-denylist.yaml) |
| F | Proposed scenario schema | [scenario-schema.md](scenario-schema.md), [../schemas/](../schemas/) (scenario, criteria, provenance), [examples/](examples/kops-net-service-endpoint-repair-001/) |
| G | Environment backend architecture | [backend-design.md](backend-design.md) |
| H | Runtime architecture | [runtime-architecture.md](runtime-architecture.md) |
| I | Initial vertical slice (10 + 2 stretch) | [vertical-slice.md](vertical-slice.md) |
| J | Reuse / rejection / read-only lists | [reuse-register.md](reuse-register.md) |

---

## A. Repository inventory — headline findings

Eight repositories were audited at pinned commits by reading code paths, not READMEs. All `references/` working trees were verified clean afterwards.

| Repo | License (verified) | Tasks | Contamination | KOPS use |
|---|---|---|---|---|
| grindxhq-cka | Apache-2.0 | 86 | low–med | ideas (code reuse possible, not planned) |
| k16s | PolyForm NC | 87 | low–med | architecture only |
| ck-x | BSL 1.1 (MIT before 2026-05-09) | 111 | medium | architecture only |
| ckad-2026 | GPL-3.0 | **78** (not 55) | med; **Q01–16 high** | topic level; Q01–16 quarantined |
| ckad-dojo | CC BY-NC-SA | 398 | **HIGH** | **quarantined** content; architecture only |
| cka-hand-on-lab | MIT | 47 | low–med | ideas only |
| ckad-exams | **none** (badge only) | 30 | low–med | **no reuse** |
| ckad-exercises | MIT | 152 | **high (memorized)** | checklist + canary only |

**Findings that changed the brief's assumptions** (reference-inventory.md §1):
1. **ckad-dojo** holds a **verbatim killer.sh "CKAD Simulator Kubernetes 1.34"** document in git history, and killer.sh-derived scoring code at HEAD is still used as a fallback. Some of its simulations are recall-sourced.
2. **ckad-2026 Q01–Q16** share a recall-list lineage with ckad-dojo sim4.
3. **CK-X** runs **k3d/k3s**, not kind, and was **MIT** until May 2026.
4. **ckad-exams** has **no license**.
5. **K16S** runs the **control plane on the host**, so it cannot be reset per task.

## B. Cross-repository architecture comparison — conclusions

- All eight are **human simulators**. None has an agent interface, trace capture or a model-independent contract.
- **No repository has a negative control.** Only grindxhq has a solution self-test, and it runs on the wrong path and outside CI.
- **Graders are usually reachable by the candidate** (CK-X, ckad-*), or they grade a different location from the one the candidate edits (grindxhq). Either is fatal for agent evaluation.
- **"Verified" mostly means "spec fields match".** NetworkPolicy, Ingress, Gateway and HPA are graded structurally almost everywhere.
- **No system combines node/system fidelity with resettability.** KOPS B1 (`kind-node`) is designed to fill that gap.

## C. Problem-family catalog

- **72 deduplicated families** in 11 topical areas. Mode (create / modify / repair / diagnose) is an attribute, not a separate family.
- **Profile split:** 39 families are dual-profile, 26 CKA-only, 7 CKAD-only.
- **Backend split:** 56 `kind`, 11 `kind-node`, 5 `vm`.
- **Mapping:** every family carries one default competency per applicable profile, validated against the machine-readable **competency model** transcribed from CNCF curriculum **v1.35**. The PDFs are SHA-256 pinned and CC-BY attributed.
- **Invariant style:** every family lists candidate deterministic invariants, and they are behavioural wherever possible.

## D. Coverage gaps

| | CKA (27) | CKAD (24) |
|---|---|---|
| Well covered by references | 11 | 17 |
| Partial | 13 | 6 |
| Missing | 3: ARC-02 infra prep, ARC-05 HA, ARC-07 CNI/CSI/CRI | 1: AOM-01 deprecations (only in quarantined sources) |

- **The references cover the easy half.** CKA *Troubleshooting (30%)* and *Cluster Architecture (25%)* are the weakest areas. Only one of 575 non-quarantined tasks stops a real kubelet, and kubeadm upgrade, HA, OS prep and runtime failure have zero implementations.
- **Backend needs.** 11 of the 16 system-level families run on `kind-node`; only 5 need VMs.
- **v1.0 corpus sizing.** Roughly 60–80 scenarios: at least 2 per competency and at least 8 per domain per profile, with diversity before depth. Volume is not a goal.

## E. License and contamination

- **Recommended KOPS license: Apache-2.0.** Keep NC, SA, BSL and GPL code out of the core.
- **Quarantine:** ckad-dojo (entire repository and history) and ckad-2026 Q01–Q16. They are used only as a negative corpus by the contamination scanner.
- **Controls:**
  - schema constants (`copied_question: false`);
  - a provenance file per scenario;
  - a token denylist;
  - n-gram similarity scanning (fail at ≥5% vs. the quarantine corpus, warn at ≥15% vs. public repos);
  - seeded variants;
  - reviewer sign-off.
- **Proposed analysis:** a *memorization control* comparing canonical-form vs. seeded instances of a family.

## F. Scenario schema

Three JSON Schemas (2020-12) plus a validated worked example (S03).

**Structural guarantees enforced by the schema:**
- exactly one domain and competency per enabled profile, consistent with each other (generated from the competency model);
- at least one profile enabled;
- a **mandatory negative control** (`setup.confirm.must_fail`);
- a **hidden reference solution** (`const hidden`);
- every constraint is enforced by RBAC, tooling or a guard invariant;
- at least one required goal invariant;
- `pass_rule: all-required`; a verifier `error` makes the trial INVALID, never FAIL;
- pinned Kubernetes version; clean-room provenance constants;
- path-traversal protection.

**Validated during this phase:** the example passes all three schemas. Nine negative cases are rejected. Template parameters require validation on *rendered* documents, which is now part of the lint design.

## G. Backend architecture

| Class | Implementation | Covers |
|---|---|---|
| **A `kind`** | kind, pinned node-image digest, add-on profile baked offline, audit log, separate agent and verifier identities | All CKAD + object-level CKA (56 families) |
| **B1 `kind-node`** | Same kind cluster + KOPS-derived node image (sshd, etcdctl). Agent ssh from the workstation; grader via runner-side exec. **Control plane inside a disposable container.** | kubelet, containerd, static-pod control-plane faults, etcd backup/restore, certificates, static pods (11 families) |
| **B2 `vm`** | **Incus VM instances** on a Linux host, CoW snapshots, golden images per Kubernetes version (libvirt as fallback) | kubeadm upgrade, init/join, OS prep, HA, resource pressure (5 families) |

K16S was studied but **not forked**. Its privileged-LXC-workers + host-control-plane model violates the requirement that every node live in a resettable unit, and it offers no isolation. Mac developers use A/B1 locally through Docker; B2 runs on the Linux experiment host, where KVM is available.

## H. Runtime architecture

The pipeline is:

```
Registry → Loader → Backend Provisioner → Setup+Confirm → Agent Interface (Tool Gateway) → Trace Recorder → Deterministic Verifier → Result Recorder → Reset+Digest
```

- **Trial outcomes:** PASS / FAIL / **INVALID**. INVALID covers infrastructure faults; those trials are rerun and reported, never counted as FAIL.
- **The Tool Gateway is the single enforcement and recording point.** It handles budgets, tool availability and output truncation. Interface errors are counted separately from Kubernetes competence, which is crucial for 2B-class models.
- **Two tracks:**
  - **Track M (model comparison):** a fixed, versioned *Reference Scaffold* holds everything constant except model weights. This track answers the research question.
  - **Track S (agent systems):** third-party agent loops, reported separately.
- **Trace:** tool calls plus the **API audit log** (authoritative mutation record). No chain-of-thought is requested or stored.
- **Metrics (per profile, never combined):** pass@1 with CIs, pass^k, per-domain and per-competency breakdowns, and paired model comparison (McNemar, mixed-effects logistic regression). Diagnostics: failure classes, collateral damage, and the **claim–outcome gap**.
- **`kops selftest`** gates every scenario: negative control → null agent FAIL → negative solutions FAIL → oracle through the gateway as the agent identity PASS ×3 → reset digest equals baseline.

## I. Vertical slice (10 core + 2 stretch)

| | CKA | CKAD |
|---|---|---|
| Scenarios in core slice | 9, all 5 domains | 7, all 5 domains |

- **Mix:** 6 dual-profile scenarios; 8 on `kind`, 2 on `kind-node` (kubelet NotReady; scheduler static-pod fault).
- **Diversity:** each scenario is chosen to exercise a distinct pipeline element. These include connectivity matrices with positive controls, `can_i` deny matrices, stability windows, data-preservation guards, cluster-scoped guards, and seeded root-cause variants.
- **Milestones:** M0 (spikes) → M7 (pilot shake-down with 1 SLM + 1 frontier model). A pilot is a pipeline test, not a result.

## J. Reuse and rejection lists (summary)

- **Ideas reused:** 18, each attributed (reuse-register.md J.1). The key ones:
  - grindxhq's E2E self-test;
  - K16S's capability-aware denominators;
  - CK-X's exit-code step graders;
  - ckad-dojo's owned-resource manifest;
  - ckad-exams' positive and negative probes.
- **Content reused:** CNCF curriculum competency text (CC-BY 4.0, attributed).
- **Code proposed for reuse:** **none.** All Apache-2.0 candidates from grindxhq were evaluated and are recommended for reimplementation. Everything else is license-incompatible or prohibited.
- **Ideas rejected:** 17, including partial-credit primary scores, candidate-visible graders, host control planes, spec-only networking checks, runtime downloads, telemetry, LLM judges and a unified score.
- **Read-only repositories:** all 8. ckad-dojo and ckad-2026 Q01–Q16 are additionally quarantined.

---

## Decisions requested from the reviewer

Every decision point below lists the options, the trade-off, a recommendation and the reason. Details are in the linked documents.

| # | Decision | Options | Recommendation | Why | Doc |
|---|---|---|---|---|---|
| 1 | B1 (`kind-node`) counts as "system-level" for the slice | (a) yes, B2 later / (b) B2 first | **(a)** | 11/16 system families run on B1 at kind cost; B2 only adds upgrade, prep, HA and pressure | G §7 D-1 |
| 2 | B2 engine | Incus VMs / libvirt / LXD (installed here, uninitialised) | **Incus VMs** after spike S-2 | Unified images, snapshots and networks; Apache-2.0; less bespoke code | G §4 |
| 3 | Gateway/Ingress controller | Single dual-mode controller / separate controllers | **Single dual-mode**, pinned | Fewer add-ons; ingress-nginx is retired upstream | G D-3 |
| 4 | CNI | kindnet (if NetworkPolicy enforcement is verified) / Calico | Decide after measuring in spike S-1 | Behavioural NetworkPolicy checks need real enforcement | G D-4 |
| 5 | Kubernetes version | Pin 1.35 / track latest | **Pin 1.35** | Matches curriculum v1.35 | G D-5 |
| 6 | Verifier model | `verify.sh` as the verifier / declarative `criteria.yaml` + engine | **Declarative + thin `verify.sh`** | Auditability, uniform determinism controls, diagnostics | F §2 |
| 7 | Agent integration | Runtime-driven loop / agent-driven loop | **Both**, with Track M = runtime-driven Reference Scaffold | Holds the scaffold constant for model comparison | H §3 |
| 8 | Runtime language | Python / Go | **Python** | Model-serving and stats ecosystem | H §7 |
| 9 | Layout changes | Brief layout / proposed layout | **Proposed**: flat `scenarios/<id>/`, `catalog/`, `runtime/gateway/`, `workstation/`, `experiments/` | Dual-profile scenarios; the gateway as the security boundary; experiments as data | H §7 |
| 10 | KOPS license | Apache-2.0 / MIT / GPL-3.0 | **Apache-2.0** | Permissive with a patent grant; keeps the core clean | E §2 |
| 11 | Quarantine scope | As proposed / narrower | **As proposed** (ckad-dojo + history; ckad-2026 Q01–16) | Verified killer.sh and recall lineage | E §6 |
| 12 | Held-out private split | Yes from v1.0 / publish all | **Yes** | Protects against post-publication contamination | E §6 |
| 13 | Dual-profile id prefix | `kops-` / owner prefix | `kops-` | Avoids implying a primary certification | F §7 |
| 14 | Difficulty | Author-assigned 1–3 / empirical | Author-assigned now, calibrate empirically later | Needed for stratification before any data exists | F §7 |
| 15 | Partial-credit reporting | Secondary diagnostic / not at all | **Secondary, labelled** | Useful for "where does it fail" analysis without polluting PASS | F §7 |
| 16 | Mapping ambiguities (5 families) | Defaults in the catalog / alternatives | Review the defaults | These are construct-validity decisions | D §8 |

## Next steps after approval (not started)

1. Spike S-1 (kind/kind-node measurements, CNI, audit log, node faults).
2. Milestones M1–M3: registry and lint, the `kind` backend, the verifier. S01–S03 self-test green.
3. Milestones M4–M6: gateway and scaffold, then S04–S10.
4. Milestone M7: pipeline pilot.
