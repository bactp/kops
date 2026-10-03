# KOPS Blueprint Coverage Report

- **Date:** 2026-10-02
- **Data:** computed from the 60 scenarios under `scenarios/`, `docs/competency-model.yaml` (CNCF curriculum v1.35), `docs/problem-family-catalog.yaml` (72 families), `docs/cka-ckad-coverage-matrix.md` and `docs/reference-inventory.csv`.
- **Scope:** how well the current blueprint covers the CKA/CKAD syllabus, whether more scenarios can be created, and how KOPS compares with the other projects surveyed. Profiles are reported separately and never combined.
- **Validation level:** every scenario is `validated` by `kops selftest` on a **kind** cluster only. Nothing has been re-validated on the planned KubeVirt/kubeadm sandbox.

## 1. Verdict

- **Not enough yet.** Against the project's own v1.0 sizing rule (at least 2 scenarios per competency and at least 8 per domain per profile) the blueprint is about half way: 11 of 27 CKA and 11 of 24 CKAD competencies reach 2 scenarios; 22 of 27 and 21 of 24 reach at least 1.
- **Strong where a kind cluster can reach.** Workloads, configuration, services, NetworkPolicy, RBAC, storage objects, probes and logs are covered with behavioural checks, guards and wrong-fix tests.
- **Weak where the syllabus weighs most.** CKA *Troubleshooting* (30 %) and *Cluster Architecture* (25 %) get 19 % and 12 % of CKA scenarios, while *Workloads and Scheduling* (15 %) gets 44 %. Node, control-plane, etcd, certificate, kubeadm and HA tasks need `kind-node` or VM backends that are not built yet.
- **More can be created.** About 13 more scenarios fit the current backend with no new infrastructure; about 15 more need small additions (metrics-server, Helm/Kustomize, a Gateway API controller, an operator, an image-build tool); about 9 need node-level or VM backends. Detail in §6.
- **Against other projects:** KOPS has fewer scenarios than most surveyed repositories (60 vs. 30 to 398) but, among the eight repositories we audited, is the only one with a mandatory negative control, a null-agent test, wrong-fix tests and a self-test gate that every scenario must pass. It does not yet match their breadth in node-level tasks or multi-cluster sessions. Details in §5.

## 2. Inventory

| Item | Value |
|---|---|
| Scenarios | 60 (all `validated` on kind) |
| Profile mix | 35 dual-profile, 17 CKA only, 8 CKAD only |
| Difficulty 1 / 2 / 3 | 3 / 47 / 10 (author-assigned) |
| Backend | 53 single-node kind, 7 with extra worker nodes |
| Problem families touched | 46 of 72 |
| With at least one behavioural or state-effect check | 48 of 60 |
| With a guard (unchanged resource or denied permission) | 36 of 60 |
| With 2 or more injected faults | 13 of 60 |
| Wrong-fix tests per scenario | 2 for 54, 3 for 3, 1 for 2, none for 1 |
| Weak verification (no behavioural check) | 12 scenarios, listed in §7 |

## 3a. CKA: coverage against the syllabus

| Domain | Syllabus weight | Scenarios (primary) | Share of scenarios | Share minus weight | Competencies with ≥1 / total | Competencies with ≥2 | Meets ≥8 target |
|---|---|---|---|---|---|---|---|
| Storage | 10 % | 4 | 7.7 % | -2.3 pts | 3 / 3 | 1 | no |
| Troubleshooting | 30 % | 10 | 19.2 % | -10.8 pts | 5 / 5 | 2 | yes |
| Workloads and Scheduling | 15 % | 23 | 44.2 % | +29.2 pts | 5 / 5 | 4 | yes |
| Cluster Architecture, Installation and Configuration | 25 % | 6 | 11.5 % | -13.5 pts | 4 / 8 | 1 | no |
| Servicing and Networking | 20 % | 9 | 17.3 % | -2.7 pts | 5 / 6 | 3 | yes |
| **Total** | 100 % | **52** | | | 22 / 27 | 11 | |

Counts use each scenario's *primary* competency for CKA. Dual-profile scenarios appear in both profile tables.

### Per competency (CKA)

| Competency | Text | KOPS scenarios | Reference repos with tasks | Reference verification class | Min. backend (catalog) |
|---|---|---|---|---|---|
| **Storage (10 %)** | | | | | |
| CKA-STO-01 | Implement storage classes and dynamic volume provisioning | 1 | 4 | partial | kind |
| CKA-STO-02 | Configure volume types, access modes and reclaim policies | 1 | 7 | partial | kind |
| CKA-STO-03 | Manage persistent volumes and persistent volume claims | 2 | 7 | well | kind |
| **Troubleshooting (30 %)** | | | | | |
| CKA-TRB-01 | Troubleshoot clusters and nodes | 1 | 3 | partial | kind-node / vm |
| CKA-TRB-02 | Troubleshoot cluster components | 1 | 3 | partial | kind-node |
| CKA-TRB-03 | Monitor cluster and application resource usage | 1 | 5 | partial | kind |
| CKA-TRB-04 | Manage and evaluate container output streams | 3 | 7 | well | kind |
| CKA-TRB-05 | Troubleshoot services and networking | 4 | 4 | well | kind |
| **Workloads and Scheduling (15 %)** | | | | | |
| CKA-WLS-01 | Understand application deployments and how to perform rolling… | 3 | 6 | well | kind |
| CKA-WLS-02 | Use ConfigMaps and Secrets to configure applications | 3 | 7 | well | kind |
| CKA-WLS-03 | Configure workload autoscaling | 1 | 5 | partial | kind |
| CKA-WLS-04 | Understand the primitives used to create robust, self-healing… | 9 | 7 | well | kind / kind-node |
| CKA-WLS-05 | Configure Pod admission and scheduling (limits, node affinity… | 7 | 7 | well | kind |
| **Cluster Architecture, Installation and Configuration (25 %)** | | | | | |
| CKA-ARC-01 | Manage role based access control (RBAC) | 3 | 6 | well | kind |
| CKA-ARC-02 | Prepare underlying infrastructure for installing a Kubernetes… | 0 ⚠ | 0 | missing | vm |
| CKA-ARC-03 | Create and manage Kubernetes clusters using kubeadm | 0 ⚠ | 3 | partial | kind-node / vm |
| CKA-ARC-04 | Manage the lifecycle of Kubernetes clusters | 1 | 3 | partial | kind / kind-node / vm |
| CKA-ARC-05 | Implement and configure a highly-available control plane | 0 ⚠ | 0 | missing | vm |
| CKA-ARC-06 | Use Helm and Kustomize to install cluster components | 0 ⚠ | 5 | partial | kind |
| CKA-ARC-07 | Understand extension interfaces (CNI, CSI, CRI, etc.) | 1 | 0 | missing | kind-node |
| CKA-ARC-08 | Understand CRDs, install and configure operators | 1 | 5 | partial | kind |
| **Servicing and Networking (20 %)** | | | | | |
| CKA-NET-01 | Understand connectivity between Pods | 1 | 2 | partial | kind |
| CKA-NET-02 | Define and enforce Network Policies | 2 | 7 | well | kind |
| CKA-NET-03 | Use ClusterIP, NodePort, LoadBalancer service types and endpo… | 3 | 7 | well | kind |
| CKA-NET-04 | Use the Gateway API to manage Ingress traffic | 0 ⚠ | 3 | partial | kind |
| CKA-NET-05 | Know how to use Ingress controllers and Ingress resources | 1 | 7 | well | kind |
| CKA-NET-06 | Understand and use CoreDNS | 2 | 4 | partial | kind |

## 3b. CKAD: coverage against the syllabus

| Domain | Syllabus weight | Scenarios (primary) | Share of scenarios | Share minus weight | Competencies with ≥1 / total | Competencies with ≥2 | Meets ≥8 target |
|---|---|---|---|---|---|---|---|
| Application Design and Build | 20 % | 8 | 18.6 % | -1.4 pts | 3 / 4 | 3 | yes |
| Application Deployment | 20 % | 5 | 11.6 % | -8.4 pts | 2 / 4 | 2 | no |
| Application Observability and Maintenance | 15 % | 8 | 18.6 % | +3.6 pts | 5 / 5 | 2 | yes |
| Application Environment, Configuration and Security | 25 % | 11 | 25.6 % | +0.6 pts | 8 / 8 | 2 | yes |
| Services and Networking | 20 % | 11 | 25.6 % | +5.6 pts | 3 / 3 | 2 | yes |
| **Total** | 100 % | **43** | | | 21 / 24 | 11 | |

Counts use each scenario's *primary* competency for CKAD. Dual-profile scenarios appear in both profile tables.

### Per competency (CKAD)

| Competency | Text | KOPS scenarios | Reference repos with tasks | Reference verification class | Min. backend (catalog) |
|---|---|---|---|---|---|
| **Application Design and Build (20 %)** | | | | | |
| CKAD-ADB-01 | Define, build and modify container images | 0 ⚠ | 4 | partial | kind |
| CKAD-ADB-02 | Choose and use the right workload resource (Deployment, Daemo… | 2 | 7 | well | kind |
| CKAD-ADB-03 | Understand multi-container Pod design patterns (e.g. sidecar,… | 3 | 6 | well | kind |
| CKAD-ADB-04 | Utilize persistent and ephemeral volumes | 3 | 7 | well | kind |
| **Application Deployment (20 %)** | | | | | |
| CKAD-ADP-01 | Use Kubernetes primitives to implement common deployment stra… | 2 | 2 | partial | kind |
| CKAD-ADP-02 | Understand Deployments and how to perform rolling updates | 3 | 6 | well | kind |
| CKAD-ADP-03 | Use the Helm package manager to deploy existing packages | 0 ⚠ | 5 | partial | kind |
| CKAD-ADP-04 | Kustomize | 0 ⚠ | 3 | partial | kind |
| **Application Observability and Maintenance (15 %)** | | | | | |
| CKAD-AOM-01 | Understand API depreciations | 1 | 0 | missing | kind |
| CKAD-AOM-02 | Implement probes and health checks | 2 | 5 | well | kind |
| CKAD-AOM-03 | Use built-in CLI tools to monitor Kubernetes applications | 1 | 5 | partial | kind |
| CKAD-AOM-04 | Utilize container logs | 1 | 4 | well | kind |
| CKAD-AOM-05 | Debugging in Kubernetes | 3 | 6 | well | kind |
| **Application Environment, Configuration and Security (25 %)** | | | | | |
| CKAD-AEC-01 | Discover and use resources that extend Kubernetes (CRD, Opera… | 1 | 5 | partial | kind |
| CKAD-AEC-02 | Understand authentication, authorization and admission control | 3 | 6 | well | kind |
| CKAD-AEC-03 | Understand requests, limits, quotas | 1 | 6 | well | kind |
| CKAD-AEC-04 | Define resource requirements | 1 | 7 | well | kind |
| CKAD-AEC-05 | Understand ConfigMaps | 2 | 6 | well | kind |
| CKAD-AEC-06 | Create & consume Secrets | 1 | 6 | well | kind |
| CKAD-AEC-07 | Understand ServiceAccounts | 1 | 4 | well | kind |
| CKAD-AEC-08 | Understand Application Security (SecurityContexts, Capabiliti… | 1 | 5 | well | kind |
| **Services and Networking (20 %)** | | | | | |
| CKAD-SNW-01 | Demonstrate basic understanding of NetworkPolicies | 3 | 7 | well | kind |
| CKAD-SNW-02 | Provide and troubleshoot access to applications via services | 7 | 7 | well | kind |
| CKAD-SNW-03 | Use Ingress rules to expose applications | 1 | 7 | well | kind |

## 4. Balance if the blueprint grew to 100 scenarios per profile

Illustrative: how many scenarios each domain would hold if the mix followed the syllabus weights, against today's counts (dual-profile scenarios counted in both).

**CKA**

| Domain | Target at 100 | Today | Gap |
|---|---|---|---|
| Storage | 10 | 4 | +6 |
| Troubleshooting | 30 | 10 | +20 |
| Workloads and Scheduling | 15 | 23 | -8 |
| Cluster Architecture, Installation and Configuration | 25 | 6 | +19 |
| Servicing and Networking | 20 | 9 | +11 |

**CKAD**

| Domain | Target at 100 | Today | Gap |
|---|---|---|---|
| Application Design and Build | 20 | 8 | +12 |
| Application Deployment | 20 | 5 | +15 |
| Application Observability and Maintenance | 15 | 8 | +7 |
| Application Environment, Configuration and Security | 25 | 11 | +14 |
| Services and Networking | 20 | 11 | +9 |

A positive gap means more scenarios are needed. *Workloads and Scheduling* is already above its weight; Troubleshooting and Cluster Architecture carry the largest gaps, and those depend on node-level and VM capabilities.

## 5. Comparison with other projects

### 5.1 Surveyed repositories (audited at pinned commits) and newly found ones

| Project | Licence | Audience | Tasks (as audited) | Cluster model | Version pinned | Verification | Negative control | Self-test | Agent interface |
|---|---|---|---|---|---|---|---|---|---|
| grindxhq-cka | Apache-2.0 | CKA | 86 (359 checks) | kind clusters + bastion | no | shell command + matcher, on host | no | E2E runner, not in CI | no |
| k16s | PolyForm NC | CKA/CKS | 87 | kubeadm control plane on host, LXC workers | yes (1.33) | `validate.sh` exit code | no | 1 lint test | no |
| ck-x | BSL 1.1 | CKA/CKAD/CKS | 111 (329 steps) | k3d in Docker | no | exit code per step, on jumphost | no | none | no |
| ckad-2026 | GPL-3.0 | CKAD | 78 | existing cluster | no | jsonpath comparisons, always exit 0 | no | none | no |
| ckad-dojo | CC BY-NC-SA | CKAD | 398 (quarantined) | existing cluster | no | bash scoring, keyword heuristics | no | CI lint + pytest | no |
| cka-hand-on-lab | MIT | CKA | 47 | single-node minikube | no | substring match (4 always pass) | no | none | no |
| ckad-exams | none | CKAD | 30 | single cluster | no | bash validators with probes | no | none | no |
| ckad-exercises | MIT | CKAD | 152 | any | no | none (self-check) | no | none | no |
| ckad-killercoda (omkar-shelke25) | MIT | CKAD | not stated; many topic folders | Killercoda environment | n/a | `verify.sh` per scenario | not stated | not stated | no (Killercoda format) |
| **KOPS (this repo)** | Apache-2.0 (proposed) | CKA + CKAD, separate | **60** | fresh kind cluster per trial | **yes (1.35.8 by digest)** | typed state checks, tri-state, verifier identity | **yes, mandatory** | **yes, gate for all 60** | designed, not built |

Sources: first eight rows from `docs/reference-inventory.csv` and `docs/cross-repo-architecture-comparison.md` (our own audit); the `ckad-killercoda` row is from its public README only and has **not** been audited in depth. Killercoda and killer.sh are hosted platforms (see `docs/simulator-design.md` §2) and are not compared row by row.

Task counts are not comparable one to one: the repositories count questions, steps or checks differently, and 398 of ckad-dojo's tasks and 16 of ckad-2026's are quarantined from KOPS for contamination reasons (575 non-quarantined tasks across the eight audited repositories).

### 5.2 Competency coverage against the references

- **CKA** (27 competencies): references classify 11 as well covered, 13 partial, 3 missing. KOPS has ≥1 scenario on 22, ≥2 on 11.
- **CKAD** (24 competencies): references classify 17 as well covered, 6 partial, 1 missing. KOPS has ≥1 scenario on 21, ≥2 on 11.

Competencies where the references are *well* covered but KOPS has fewer than 2 scenarios (breadth we still owe):

| Competency | Text | KOPS | Reference repos |
|---|---|---|---|
| CKA-NET-05 | Know how to use Ingress controllers and Ingress resources | 1 | 7 |
| CKAD-AOM-04 | Utilize container logs | 1 | 4 |
| CKAD-AEC-03 | Understand requests, limits, quotas | 1 | 6 |
| CKAD-AEC-04 | Define resource requirements | 1 | 7 |
| CKAD-AEC-06 | Create & consume Secrets | 1 | 6 |
| CKAD-AEC-07 | Understand ServiceAccounts | 1 | 4 |
| CKAD-AEC-08 | Understand Application Security (SecurityContexts, Capabiliti… | 1 | 5 |
| CKAD-SNW-03 | Use Ingress rules to expose applications | 1 | 7 |

Competencies the references leave *missing or partial* where KOPS already has a scenario (the gap KOPS was designed to fill):

| Competency | Text | Reference class | KOPS scenarios |
|---|---|---|---|
| CKA-STO-01 | Implement storage classes and dynamic volume provisioning | partial | 1 |
| CKA-STO-02 | Configure volume types, access modes and reclaim policies | partial | 1 |
| CKA-TRB-01 | Troubleshoot clusters and nodes | partial | 1 |
| CKA-TRB-02 | Troubleshoot cluster components | partial | 1 |
| CKA-TRB-03 | Monitor cluster and application resource usage | partial | 1 |
| CKA-WLS-03 | Configure workload autoscaling | partial | 1 |
| CKA-ARC-04 | Manage the lifecycle of Kubernetes clusters | partial | 1 |
| CKA-ARC-07 | Understand extension interfaces (CNI, CSI, CRI, etc.) | missing | 1 |
| CKA-ARC-08 | Understand CRDs, install and configure operators | partial | 1 |
| CKA-NET-01 | Understand connectivity between Pods | partial | 1 |
| CKA-NET-06 | Understand and use CoreDNS | partial | 2 |
| CKAD-ADP-01 | Use Kubernetes primitives to implement common deployment stra… | partial | 2 |
| CKAD-AOM-01 | Understand API depreciations | missing | 1 |
| CKAD-AOM-03 | Use built-in CLI tools to monitor Kubernetes applications | partial | 1 |
| CKAD-AEC-01 | Discover and use resources that extend Kubernetes (CRD, Opera… | partial | 1 |

Competencies that nobody covers well and KOPS has not reached yet: CKA-ARC-02, CKA-ARC-05.

### 5.3 What KOPS does differently (mechanism, not volume)

| Property | Surveyed repositories | KOPS today |
|---|---|---|
| Proof the broken state is really broken (negative control) | none of the eight | required for every scenario; checked on every trial |
| Proof the task is solvable and the verifier is not vacuous | only grindxhq has a solution runner | null agent must FAIL, wrong fixes must FAIL, reference solution must PASS three times, for every scenario |
| Where grading runs | usually where the candidate works, or on a different file system | separate verifier credentials, after the agent session |
| What is checked | mostly spec fields or strings | endpoints, HTTP and DNS probes from client pods, logs, placement, access reviews, plus guards against shortcuts |
| Reset | partial, none, or whole-cluster rebuild | fresh cluster destroyed after every trial, container absence verified |
| Version pinning | mostly none | node image pinned by digest, recorded in each result |
| Trace for later analysis | none | every command, output and classification |
| Breadth | 30 to 398 tasks, with node-level tasks in a few (k16s, grindxhq) | 60 scenarios, node-level tasks mostly missing |
| Multi-cluster sessions | grindxhq (1 to 4 clusters) | designed, not built |
| Documentation access inside the environment | grindxhq proxies docs | designed (offline mirror), not built |

## 6. Can more scenarios be created?

Yes. The unimplemented problem families and competency deficits split by what they need.

### 6.1 The 26 problem families without a scenario

| Needs | Families |
|---|---|
| Now, on the current backend | PF-WKL-001 Create or configure a Deployment (replicas, label… (contamination risk: high); PF-WKL-005 Run batch workloads with Job (completions, parall… (contamination risk: high); PF-WKL-010 Configure container command/args, env and lifecyc… (contamination risk: medium); PF-STO-004 Mount persistent and ephemeral volumes in Pods (P… (contamination risk: high); PF-SCH-001 Place Pods on nodes (nodeSelector, node affinity … (contamination risk: medium) |
| candidate files/stdin (CSR manifest) | PF-SEC-007 Manage user access credentials (CSR create/approv… (contamination risk: low) |
| Gateway API controller | PF-NET-008 Manage ingress traffic with Gateway API (Gateway,… (contamination risk: low) |
| kind-node backend | PF-SCH-007 Run static Pods on a specific node (kubelet-manag… (contamination risk: low); PF-CLU-001 Back up etcd (snapshot save with correct endpoint… (contamination risk: high); PF-CLU-002 Restore etcd from snapshot and bring the control … (contamination risk: medium); PF-CLU-007 Manage cluster certificates (inspect expiry, rene… (contamination risk: medium); PF-CLU-008 Change control-plane configuration (apiserver fla… (contamination risk: low); PF-NOD-001 Recover a NotReady node caused by kubelet failure… (contamination risk: medium); PF-NOD-002 Recover from container runtime failure (container… (contamination risk: low); PF-NOD-003 Repair a failed control-plane component (static-p… (contamination risk: high) |
| metrics-server add-on | PF-OBS-003 Monitor resource usage with built-in tools (kubec… (contamination risk: low) |
| Helm binary and offline chart repository | PF-PKG-001 Deploy and manage packages with Helm (install/upg… (contamination risk: medium); PF-PKG-002 Repair failed or pending Helm releases (contamination risk: low) |
| Kustomize with files | PF-PKG-003 Customize manifests with Kustomize (bases/overlay… (contamination risk: low) |
| offline operator image | PF-EXT-002 Install and configure an operator and drive it th… (contamination risk: low) |
| container image build tool | PF-IMG-001 Define, build and modify container images (Docker… (contamination risk: medium) |
| VM backend | PF-CLU-003 Upgrade a kubeadm cluster (control plane then wor… (contamination risk: medium); PF-CLU-004 Create and extend clusters with kubeadm (init, jo… (contamination risk: low); PF-CLU-005 Prepare node infrastructure for installing Kubern… (contamination risk: low); PF-CLU-006 Implement a highly-available control plane (addit… (contamination risk: low); PF-NOD-004 Handle node resource pressure and eviction (disk/… (contamination risk: low) |

Families marked contamination risk *high* (Deployment, Job, volume mounting) are the forms most memorised from public material. They need seeded parameters, several faults and shortcut guards, as the design already requires.

### 6.2 Scenarios needed to reach 2 per competency

| Needs | CKA | CKAD |
|---|---|---|
| Current backend, no new infrastructure | 5 (STO-01, STO-02, ARC-07, NET-01, NET-05) | 8 (AOM-01, AOM-04, AEC-03, AEC-04, AEC-06, AEC-07, AEC-08, SNW-03) |
| Metrics-server add-on | 2 (TRB-03, WLS-03) | 1 (AOM-03) |
| Helm and Kustomize tooling | 2 (ARC-06) | 4 (ADP-03, ADP-04) |
| Gateway API controller | 2 (NET-04) | none |
| Offline operator | 1 (ARC-08) | 1 (AEC-01) |
| Image build tool | none | 2 (ADB-01) |
| `kind-node` backend | 4 (TRB-01, TRB-02, ARC-04, ARC-03) | none |
| VM backend | 5 (ARC-02, ARC-03, ARC-05) | none |
| **Total** | **21** | **16** |

Totals are the deficits against 2 scenarios per competency. The "current backend" rows can start immediately; `SNW-03` (Ingress) would be spec-only without a controller.

### 6.3 Beyond the minimum

- The ≥8 per domain rule is not met for CKA Storage (4), CKA Cluster Architecture (6), and for CKAD Deployment (5). Storage has only 4 families, so reaching 8 needs further variants of the same families, which are not independent samples (see the held-out split decision).
- The scenarios written in the last session are one seeded instance per family. Many existing families can host a second, harder variant (different fault mix, distractors, recovery after a wrong first action) without new infrastructure.
- Two gateway limits, reported by the authoring run, block whole classes of tasks: no file or stdin input, so create-from-manifest tasks (NetworkPolicy, PVC, StatefulSet creation) stay in the backlog; and `--as` is forbidden, so an agent cannot self-check RBAC with `can-i`. Adding a workstation capability (files and stdin) unlocks the create variants. This is the same capability the platform needs for human practice.

### 6.4 Suggested order

1. Rebalance on the current backend: the 13 scenarios in §6.2 first row, favouring CKA Storage and the weakest CKAD competencies.
2. Add metrics-server and file/stdin to the workstation profile, then the 3 metrics-server scenarios and the create-type variants they unlock.
3. Build the `kind-node` capability (ssh, node exec) for the Troubleshooting and Architecture gaps, the largest weighted gaps in the syllabus.
4. Helm, Kustomize, Gateway API and operator tooling for the Architecture and Deployment domains.
5. VM backend for upgrade, kubeadm install, OS preparation and HA.
6. Re-validate every scenario on the KubeVirt/kubeadm sandbox before it is offered to users.

## 7. Caveats

- **Validation is on kind only.** CNI, storage class and node layout differ on the planned sandbox. The scenarios most likely to behave differently: NetworkPolicy, storage and scheduling scenarios (see `docs/scenario-backlog.md` §6.1).
- **Primary-competency counting.** A scenario counts once per profile for its primary competency; secondary skills are not counted, so coverage of sub-skills is understated.
- **Families as a proxy.** A family covered by one scenario is not fully covered.
- **Author-assigned difficulty** and **no human review yet** of the scenarios written by the authoring agent; selftest proves the verifier works, not that the task text is good or the difficulty right.
- **Comparison is by mechanism and by topic,** not by task content. Quarantined sources were not read, and no text similarity analysis against the other projects has been run.
- **Newly found projects** (`ckad-killercoda`, Killercoda, killer.sh) were not audited at code level.
- Scenarios with no behavioural check (12): `cka-arc-extension-interfaces-report-001`, `cka-sto-default-class-001`, `cka-sto-reclaim-retain-001`, `cka-trb-node-capacity-diagnose-001`, `cka-wl-hpa-spec-001`, `cka-wl-pdb-protect-001`, `ckad-deploy-canary-share-001`, `ckad-obs-api-deprecation-001`, `ckad-obs-cli-report-001`, `kops-ext-crd-discover-001`, `kops-net-ingress-rules-001`, `kops-obs-multicontainer-findings-001`. Three are spec-only by construction (HPA, Ingress, API deprecation) because the current kind profile has no metrics server or controller.

