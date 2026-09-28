# CKA / CKAD Coverage Matrix (C/D)

This matrix shows, for every public competency (CNCF curriculum v1.35, [`competency-model.yaml`](competency-model.yaml)):

- the KOPS problem families that target it ([`problem-family-catalog.yaml`](problem-family-catalog.yaml));
- how many audited reference repositories contain such tasks;
- how deeply those references actually **verify** them;
- the minimum KOPS backend class;
- which vertical-slice scenario covers it ([`vertical-slice.md`](vertical-slice.md)). Entries marked `*` are stretch scenarios.

The tables were generated from the two YAML files; only the "verification depth" and "coverage class" columns are audit judgements. Profiles are shown separately and are **never combined**.

**Columns**

- **Ref. repos** counts non-quarantined appearances across the 8 repos. ckad-dojo and ckad-2026 Q01–Q16 are excluded.
- **Ref. verification depth** is the audit judgement of how well the *references* check this competency:
  - `exec/state`: live state checked;
  - `spec-only`: object fields checked but no behaviour;
  - `artifact`: an answer file is checked.
- **Coverage class**:
  - `well`: at least 4 repos with executable checks;
  - `partial`: some coverage, but shallow, online-dependent or missing sub-skills;
  - `missing`: no usable reference.

## CKA profile (curriculum v1.35)

| Competency | Text (verbatim) | Families | Ref. repos | Ref. verification depth | Coverage class | Min. backend | Slice |
|---|---|---|---|---|---|---|---|
| **Storage (10%)** | | | | | | | |
| CKA-STO-01 | Implement storage classes and dynamic volume provisioning | PF-STO-001 | 4 | exec/spec | partial | kind | — |
| CKA-STO-02 | Configure volume types, access modes and reclaim policies | PF-STO-003, PF-STO-004 | 7 | exec/spec | partial | kind | — |
| CKA-STO-03 | Manage persistent volumes and persistent volume claims | PF-STO-002 | 7 | exec/state | well | kind | S07 |
| **Troubleshooting (30%)** | | | | | | | |
| CKA-TRB-01 | Troubleshoot clusters and nodes | PF-NOD-001, PF-NOD-002, PF-NOD-004, PF-NOD-005 | 3 | 1 real (K16S kubelet stop); grindxhq fakes via cordon | partial | kind-node / vm | S09 |
| CKA-TRB-02 | Troubleshoot cluster components | PF-NET-011, PF-NOD-003 | 3 | static-pod faults in 2 repos (+1 not injected) | partial | kind-node | S10 |
| CKA-TRB-03 | Monitor cluster and application resource usage | PF-OBS-003, PF-OBS-006 | 5 | artifact-only, metrics noisy | partial | kind | — |
| CKA-TRB-04 | Manage and evaluate container output streams | PF-OBS-002, PF-OBS-004 | 7 | exec/state | well | kind | — |
| CKA-TRB-05 | Troubleshoot services and networking | PF-NET-003, PF-NET-006 | 4 | exec/state (endpoints); little behavioural | well | kind | S03 |
| **Workloads and Scheduling (15%)** | | | | | | | |
| CKA-WLS-01 | Understand application deployments and how to perform rolling update and rollbacks | PF-WKL-002, PF-WKL-003 | 6 | exec/state | well | kind | S02 |
| CKA-WLS-02 | Use ConfigMaps and Secrets to configure applications | PF-CFG-001, PF-CFG-002 | 7 | exec/spec | well | kind | S01 |
| CKA-WLS-03 | Configure workload autoscaling | PF-WKL-011 | 5 | spec-only | partial | kind | — |
| CKA-WLS-04 | Understand the primitives used to create robust, self-healing, application deployments | PF-WKL-001, PF-WKL-005, PF-WKL-006, PF-WKL-007, PF-WKL-008, PF-WKL-009, PF-WKL-012, PF-SCH-007, PF-OBS-001 | 7 | exec/state | well | kind / kind-node | — |
| CKA-WLS-05 | Configure Pod admission and scheduling (limits, node affinity, etc.) | PF-CFG-004, PF-CFG-005, PF-SEC-006, PF-SCH-001, PF-SCH-002, PF-SCH-003, PF-SCH-004, PF-SCH-005 | 7 | exec/state | well | kind | S05 |
| **Cluster Architecture, Installation and Configuration (25%)** | | | | | | | |
| CKA-ARC-01 | Manage role based access control (RBAC) | PF-SEC-001, PF-SEC-002, PF-SEC-003, PF-SEC-007 | 6 | spec + few can-i | well | kind | S08 |
| CKA-ARC-02 | Prepare underlying infrastructure for installing a Kubernetes cluster | PF-CLU-005 | 0 | none | missing | vm | — |
| CKA-ARC-03 | Create and manage Kubernetes clusters using kubeadm | PF-CLU-004, PF-CLU-008 | 3 | config files only | partial | kind-node / vm | — |
| CKA-ARC-04 | Manage the lifecycle of Kubernetes clusters | PF-SCH-006, PF-CLU-001, PF-CLU-002, PF-CLU-003, PF-CLU-007 | 3 | etcd backup yes; restore partial; upgrade none; certs inspect | partial | kind / kind-node / vm | S12* |
| CKA-ARC-05 | Implement and configure a highly-available control plane | PF-CLU-006 | 0 | none | missing | vm | — |
| CKA-ARC-06 | Use Helm and Kustomize to install cluster components | PF-PKG-001, PF-PKG-002, PF-PKG-003 | 5 | online charts; spec | partial | kind | — |
| CKA-ARC-07 | Understand extension interfaces (CNI, CSI, CRI, etc.) | PF-EXT-003 | 0 | none | missing | kind-node | — |
| CKA-ARC-08 | Understand CRDs, install and configure operators | PF-EXT-001, PF-EXT-002 | 5 | CRD yes; operators none | partial | kind | — |
| **Servicing and Networking (20%)** | | | | | | | |
| CKA-NET-01 | Understand connectivity between Pods | PF-NET-010 | 2 | 2 repos, artifact-ish | partial | kind | — |
| CKA-NET-02 | Define and enforce Network Policies | PF-NET-004, PF-NET-005 | 7 | mostly spec-only; few behavioural probes | well | kind | S06 |
| CKA-NET-03 | Use ClusterIP, NodePort, LoadBalancer service types and endpoints | PF-NET-001, PF-NET-002 | 7 | exec/state | well | kind | — |
| CKA-NET-04 | Use the Gateway API to manage Ingress traffic | PF-NET-008 | 3 | spec-only (no controller) | partial | kind | — |
| CKA-NET-05 | Know how to use Ingress controllers and Ingress resources | PF-NET-007 | 7 | mostly spec-only | well | kind | — |
| CKA-NET-06 | Understand and use CoreDNS | PF-NET-009 | 4 | exec/state | partial | kind | S11* |

## CKAD profile (curriculum v1.35)

| Competency | Text (verbatim) | Families | Ref. repos | Ref. verification depth | Coverage class | Min. backend | Slice |
|---|---|---|---|---|---|---|---|
| **Application Design and Build (20%)** | | | | | | | |
| CKAD-ADB-01 | Define, build and modify container images | PF-IMG-001 | 4 | host docker; artifact | partial | kind | — |
| CKAD-ADB-02 | Choose and use the right workload resource (Deployment, DaemonSet, CronJob, etc.) | PF-WKL-001, PF-WKL-005, PF-WKL-006, PF-WKL-007, PF-WKL-010 | 7 | exec/state | well | kind | — |
| CKAD-ADB-03 | Understand multi-container Pod design patterns (e.g. sidecar, init and others) | PF-WKL-008, PF-WKL-009 | 6 | exec/state | well | kind | — |
| CKAD-ADB-04 | Utilize persistent and ephemeral volumes | PF-CFG-003, PF-STO-001, PF-STO-002, PF-STO-004 | 7 | exec/state | well | kind | S07 |
| **Application Deployment (20%)** | | | | | | | |
| CKAD-ADP-01 | Use Kubernetes primitives to implement common deployment strategies (e.g. blue/green or canary) | PF-WKL-004 | 2 | 1 non-quarantined item | partial | kind | — |
| CKAD-ADP-02 | Understand Deployments and how to perform rolling updates | PF-WKL-002, PF-WKL-003 | 6 | exec/state | well | kind | S02 |
| CKAD-ADP-03 | Use the Helm package manager to deploy existing packages | PF-PKG-001, PF-PKG-002 | 5 | online charts | partial | kind | — |
| CKAD-ADP-04 | Kustomize | PF-PKG-003 | 3 | spec | partial | kind | — |
| **Application Observability and Maintenance (15%)** | | | | | | | |
| CKAD-AOM-01 | Understand API depreciations | PF-OBS-005 | 0 | quarantined sources only | missing | kind | — |
| CKAD-AOM-02 | Implement probes and health checks | PF-OBS-001 | 5 | exec/spec; racy | well | kind | S04 |
| CKAD-AOM-03 | Use built-in CLI tools to monitor Kubernetes applications | PF-OBS-003, PF-OBS-006 | 5 | artifact-only | partial | kind | — |
| CKAD-AOM-04 | Utilize container logs | PF-OBS-002 | 4 | artifact/log grep | well | kind | — |
| CKAD-AOM-05 | Debugging in Kubernetes | PF-SCH-005, PF-OBS-004 | 6 | exec/state | well | kind | — |
| **Application Environment, Configuration and Security (25%)** | | | | | | | |
| CKAD-AEC-01 | Discover and use resources that extend Kubernetes (CRD, Operators) | PF-EXT-001, PF-EXT-002 | 5 | CRD yes; operators none | partial | kind | — |
| CKAD-AEC-02 | Understand authentication, authorization and admission control | PF-SEC-001, PF-SEC-002, PF-SEC-003, PF-SEC-006, PF-SEC-007 | 6 | spec + few can-i | well | kind | S08 |
| CKAD-AEC-03 | Understand requests, limits, quotas | PF-CFG-005 | 6 | exec/state | well | kind | — |
| CKAD-AEC-04 | Define resource requirements | PF-CFG-004 | 7 | exec/spec | well | kind | — |
| CKAD-AEC-05 | Understand ConfigMaps | PF-CFG-001 | 6 | exec/spec | well | kind | S01 |
| CKAD-AEC-06 | Create & consume Secrets | PF-CFG-002 | 6 | exec/spec | well | kind | — |
| CKAD-AEC-07 | Understand ServiceAccounts | PF-SEC-004 | 4 | spec | well | kind | — |
| CKAD-AEC-08 | Understand Application Security (SecurityContexts, Capabilities, etc.) | PF-SEC-005 | 5 | spec | well | kind | — |
| **Services and Networking (20%)** | | | | | | | |
| CKAD-SNW-01 | Demonstrate basic understanding of NetworkPolicies | PF-NET-004, PF-NET-005, PF-NET-006 | 7 | mostly spec-only; few behavioural probes | well | kind | S06 |
| CKAD-SNW-02 | Provide and troubleshoot access to applications via services | PF-NET-001, PF-NET-002, PF-NET-003, PF-NET-010 | 7 | exec/state | well | kind | S03 |
| CKAD-SNW-03 | Use Ingress rules to expose applications | PF-NET-007 | 7 | mostly spec-only | well | kind | — |

## Summary

| | CKA (27 competencies) | CKAD (24 competencies) |
|---|---|---|
| Well covered by references | 11 | 17 |
| Partially covered | 13 | 6 |
| Missing in references | 3 (ARC-02, ARC-05, ARC-07) | 1 (AOM-01: only quarantined sources) |
| Families targeting the profile | 65 | 46 |
| Competencies needing `kind-node` or `vm` for at least one family | 6 (TRB-01, TRB-02, WLS-04 via static pods, ARC-03, ARC-04, ARC-07) + 2 vm-only (ARC-02, ARC-05) | 0 |
| Competencies covered by the core vertical slice (S01–S10) | 9 (all 5 domains) | 7 (all 5 domains) |

**Observations**

1. **The references are strongly skewed toward what is easy to build on a single cluster.** CKAD is well covered (17/24), while CKA's heaviest domain, *Troubleshooting (30%)*, and *Cluster Architecture (25%)* are the weakest. Only **one** of the 575 non-quarantined reference tasks (989 total minus 398 ckad-dojo and 16 ckad-2026 Q01–Q16) really stops kubelet on a real node (K16S `cka/01`). kubeadm upgrade, OS preparation, HA and container-runtime failure have **zero** implementations.
2. **"Covered" in a reference rarely means "verified".** NetworkPolicy, Ingress and Gateway tasks are almost always graded structurally (spec fields), and HPA is spec-only. KOPS families for these competencies specify behavioural invariants: connectivity matrices, traffic through the controller, and scaling conditions.
3. **Dual-profile families dominate** (39 of 72). KOPS's dual mapping (one competency per profile) therefore matters: the same executed scenario feeds two separate profile reports without creating a combined score.
4. **Mapping ambiguity is concentrated in a few places.** These are flagged in the catalog for review:
   - static pods (PF-SCH-007: WLS-04 vs ARC-03/TRB-01);
   - application-level pod debugging under CKA (PF-OBS-004 mapped to TRB-04, since CKA has no explicit app-debug competency);
   - Pod Security Admission under CKA (WLS-05 "Pod admission").
