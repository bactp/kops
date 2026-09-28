# Coverage-Gap Analysis (D)

This document compares the extracted problem families (72, [`problem-family-catalog.yaml`](problem-family-catalog.yaml)) against the public CKA/CKAD competency model (51 competencies, [`competency-model.yaml`](competency-model.yaml)). The per-competency table is in [`cka-ckad-coverage-matrix.md`](cka-ckad-coverage-matrix.md).

Principle from the brief: **competency coverage and operational diversity, not volume.**

---

## 1. Well-covered competencies

These have at least 4 reference repositories with executable checks. KOPS needs clean-room authoring and *stronger verification* here, not new ideas.

| Profile | Competencies |
|---|---|
| CKA | STO-03, TRB-04, TRB-05, WLS-01, WLS-02, WLS-04, WLS-05, ARC-01, NET-02, NET-03, NET-05 |
| CKAD | ADB-02, ADB-03, ADB-04, ADP-02, AOM-02, AOM-04, AOM-05, AEC-02 … AEC-08, SNW-01, SNW-02, SNW-03 |

**Risk in this zone: contamination, not coverage.** Seven of the eight `high`-risk families live here: Deployment, Job, Service, Service repair, volumes, pod debugging, and the control-plane manifest fix. These are the forms most memorized from public prep material. Required mitigations:
1. seeded parameters (names, ports, images, revision numbers);
2. multi-fault variants (e.g., selector **and** targetPort);
3. guards that block shortcut fixes (no delete/recreate, no policy deletion, no cluster-admin);
4. behavioural invariants instead of spec strings;
5. the contamination scan in lint.

## 2. Partially-covered competencies

| Competency | What is missing in the references | KOPS action |
|---|---|---|
| CKA-TRB-01 Troubleshoot clusters and nodes | One real kubelet fault (K16S). grindxhq fakes NotReady with a cordon. No runtime failure, no node loss. | PF-NOD-001/002/005 on `kind-node`. Vary root causes. |
| CKA-TRB-02 Troubleshoot cluster components | Static-pod faults exist, but K16S injects them into the grader's host and cka-hand-on-lab never injects them. No kube-proxy/CNI faults. | PF-NOD-003 and PF-NET-011 on `kind-node`, with behavioural recovery checks. |
| CKA-TRB-03 Monitor resource usage | Artifact-only, and metrics are noisy. | Seed usage gaps of 10× or more. Prefer "act on the finding" over "write the finding". |
| CKA-WLS-03 Autoscaling | Spec-only checks. | `ScalingActive` condition plus spec. Load-driven scale-up only with a generous stability window (§5). |
| CKA-ARC-03 kubeadm clusters | Only config files are written. There is no real init or join. | PF-CLU-004 on `vm`. Experimental kind-node worker re-join (spike S-1). PF-CLU-008 (control-plane config with a behavioural effect). |
| CKA-ARC-04 Cluster lifecycle | etcd backup exists. The restore never rewires etcd (grindxhq says so explicitly). No upgrade. Certificates are inspected only. | PF-CLU-001/002/007 on `kind-node`. PF-CLU-003 upgrade on `vm`. |
| CKA-ARC-06 Helm/Kustomize | Depends on public Bitnami charts, which are fragile and changed in 2025. | KOPS-authored charts in an offline repository (`helm-repo-mirror` feature). |
| CKA-ARC-08 / CKAD-AEC-01 CRDs and operators | CRDs are covered. **Operators are not.** | PF-EXT-002 with a minimal KOPS-authored operator or a pinned upstream operator, installed offline. |
| CKA-NET-01 Pod connectivity | Two repos, artifact-style. | PF-NET-010 with a cross-node TCP matrix. |
| CKA-NET-04 Gateway API | Spec-only. None of the references installs a controller. | PF-NET-008 with a real controller (backend decision D-3) and traffic assertions. |
| CKA-NET-06 CoreDNS | Covered, but it is a cluster-scoped mutation that references never reset. | PF-NET-009 with `isolation: cluster`. |
| CKA-STO-01/02 | Dynamic provisioning and reclaim policy are thin. RWX is absent. | PF-STO-001/003. RWX is out of scope for `kind` (documented limitation). |
| CKAD-ADB-01 Images | Needs a host Docker daemon and online registries. | Rootless builder in the workstation plus an in-cluster registry (`image-registry` feature). |
| CKAD-ADP-01 Deployment strategies | One non-quarantined item. | PF-WKL-004, authored with different traffic models. |
| CKAD-ADP-03/04 Helm, Kustomize | Same as ARC-06. | Same action as ARC-06. |
| CKAD-AOM-03 CLI monitoring | Artifact-only. | Same action as TRB-03. |

## 3. Missing competencies (no usable reference)

| Competency | Why missing | KOPS family | Backend |
|---|---|---|---|
| CKA-ARC-02 Prepare underlying infrastructure | Needs per-node kernel and OS state, which container backends can't provide. | PF-CLU-005 | `vm` |
| CKA-ARC-05 HA control plane | Needs multiple control-plane nodes, a load balancer and etcd membership. | PF-CLU-006 | `vm` |
| CKA-ARC-07 Extension interfaces (CNI/CSI/CRI) | Never treated as an operational task. | PF-EXT-003 (plus PF-NOD-002 and PF-NET-011 as related troubleshooting) | `kind-node` |
| CKAD-AOM-01 API deprecations | Exists only in quarantined sources (ckad-2026 Q08, ckad-dojo). | PF-OBS-005, authored from the Kubernetes deprecation guide | `kind` |

These families also have no reference implementation: PF-CLU-003 (upgrade), PF-NOD-002 (runtime failure), PF-NOD-005 (node loss) and PF-EXT-002 (operators).

## 4. Competencies requiring node/system access

| Competency | Families | `kind-node` sufficient? | Needs `vm` |
|---|---|---|---|
| CKA-TRB-01 | PF-NOD-001, 002, 005 | ✅ | PF-NOD-004 (resource pressure) |
| CKA-TRB-02 | PF-NOD-003, PF-NET-011 | ✅ | — |
| CKA-WLS-04 (static pods only) | PF-SCH-007 | ✅ | — |
| CKA-ARC-03 | PF-CLU-008 ✅, PF-CLU-004 (join) | partially (re-join experimental) | PF-CLU-004 init |
| CKA-ARC-04 | PF-CLU-001, 002, 007 | ✅ | PF-CLU-003 upgrade |
| CKA-ARC-07 | PF-EXT-003 | ✅ | — |
| CKA-ARC-02 | PF-CLU-005 | ❌ | ✅ |
| CKA-ARC-05 | PF-CLU-006 | ❌ | ✅ |

**Implication.** Of the 16 system-level families, 11 run on `kind-node`. Only 5 need `vm`: CLU-003, CLU-004, CLU-005, CLU-006 and NOD-004. That is the quantitative basis for backend decision D-1: build B1 first and B2 later.

## 5. Competencies difficult to simulate deterministically

| Area | Difficulty | Mitigation, or decision to defer |
|---|---|---|
| Node resource pressure / eviction (PF-NOD-004) | Container backends share host resources, and pressure creation is non-deterministic (CK-X's version asks the user to create pressure). | **Defer** to `vm` with cgroup-limited VMs. Mark experimental. |
| HPA scaling behaviour (PF-WKL-011) | Metrics lag and load generation are timing-dependent. | Primary invariants are spec plus `ScalingActive`. Behavioural scale-up is diagnostic (non-required) unless flakiness is under 1% in self-test. |
| Metrics-based diagnosis (TRB-03, AOM-03) | Usage fluctuates. | Seed 10× usage separation, and compute the expected answer at verify time. |
| CronJob execution timing | Wall-clock schedules. | Verify spec plus a manually triggered Job. Never wait for a schedule tick. |
| LoadBalancer Services | Needs an LB implementation. | cloud-provider-kind (feature `loadbalancer`). |
| Probe correctness | "Stable" is a time-window property. | Declared `stability` windows. The self-test repeats N=3 times to measure flakiness. |
| NetworkPolicy "blocked" | Proving a negative relies on a timeout. | Several attempts with short timeouts, plus a positive control probe from the same source pod in the same verifier run. If the positive control fails, the result is `error` (INVALID), not FAIL. |
| etcd restore / control-plane repair | Recovery time varies. | Settle windows up to 180 s. Health gates. |
| Image building | Needs a builder. | Rootless podman/buildah in the workstation, with a pinned base-image cache. |
| HA / upgrade | Heavy, slow environments. | `vm` only. Run in a separate nightly track. |

## 6. Competencies appropriate for Kind (`kind`, Backend A)

56 of 72 families run on plain `kind`. That covers:

- **all 24 CKAD competencies** (with the `image-registry`, `helm-repo-mirror`, `metrics-server`, `networkpolicy`, `ingress-controller` and `default-storageclass` features);
- **19 of 27 CKA competencies** in full: all of Storage, WLS-01/02/03/05, ARC-01, ARC-06, ARC-08, all of Networking, and TRB-03/04/05. WLS-04 is also covered except for its static-pod family, which needs `kind-node`.

## 7. Recommended v1.0 corpus shape (after the vertical slice)

We are deliberately **not** proposing a volume target. The constraint is statistical and interpretive:

- **Per-competency reporting** needs several scenarios per competency, or the rate is a single-scenario anecdote. Proposal: **≥2 scenarios per competency**, drawn from distinct families where possible. Competency-level results are labelled *exploratory*.
- **Per-domain reporting is primary.** Aim for **≥8 scenarios per domain per profile.**
- **Every family gets ≥1 scenario before any family gets a 3rd.** This is diversity before depth.
- **Seeded variants multiply instances, not scenarios.** 3 seeds × k trials per scenario estimate within-scenario variance without inflating the scenario count.
- **Resulting size:** roughly **60–80 scenarios** for v1.0, covering 51/51 competencies. Of these, ~48–60 would be `kind`, ~10–14 `kind-node`, and ~4–6 `vm`, with the `vm` part reported as a separate track until B2 is validated.

## 8. Mapping ambiguities for review

| Family | Default mapping | Alternative | Why flagged |
|---|---|---|---|
| PF-SCH-007 Static pods | CKA-WLS-04 | CKA-ARC-03 / CKA-TRB-01 | The curriculum doesn't name static pods. |
| PF-OBS-004 Pod debugging (CKA side) | CKA-TRB-04 | CKA-TRB-01 | CKA has no explicit application-debug competency. |
| PF-SEC-006 Pod Security Admission (CKA side) | CKA-WLS-05 | CKA-ARC-01 | "Pod admission" wording in WLS-05. |
| PF-CFG-003 Downward API / projected (CKAD) | CKAD-ADB-04 | CKAD-AEC-05 | Ephemeral volume vs configuration. |
| PF-SCH-005 Pending diagnosis (CKA side) | CKA-WLS-05 | CKA-TRB-01 | Diagnosis vs scheduling configuration. |

The scenario-level `mapping_rationale` field is mandatory, so these decisions are recorded per scenario and can be re-analysed later without re-running experiments.
