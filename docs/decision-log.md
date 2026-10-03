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

## 2026-10-02 — Review round 3 (platform direction)

| Topic | Outcome | Consequence |
|---|---|---|
| Direction | KOPS is a **practice platform for CKA/CKAD (CKS later)**. Human experience first; agent gateway and benchmark after. | See [simulator-design.md](simulator-design.md). |
| First mode | **Practice**: per-task CHECK, hints, solution on request. Exam mode follows on the same engine. | `reference/explanation.md` and `reference/hints.md` become part of the scenario format. |
| Frontend | No constraints. Proposal: SPA with xterm.js, code-server, FastAPI backend sharing the Python package. | |
| Scenarios | A background agent authors many scenarios and a backlog of designs, under `scenarios/` and `docs/scenario-backlog.md`. | Results to be reviewed before commit. |
| Reference check | Killercoda's own page states that interactive environments use VMs scheduled with KubeVirt. | Informs the VmProvider tier. |

| Workstation toolset (P2) | kubectl + alias `k`, bash + bash-completion, `yq`, `curl`, `wget`, `man`, `ssh`, plus `vim`, `jq`, `helm` as practice extras | Exam-faithful tools verified against the Linux Foundation page; extras flagged as not on the official list. |
| Editor | code-server | |
| Playground mode | Yes: 1 sandbox per user, 1 control plane + 1 worker, TTL 1–2 h with extend, reset, stop, delete. Practice/Exam stay clean-per-task. | Not graded; never reused for tasks. |

## 2026-10-02 — Review round 4 (open questions closed)

| Topic | Outcome | Consequence |
|---|---|---|
| Terminal for node-level tasks | Model is workstation → ssh → designated host. MVP on kind may simplify the connection, but the terminal/session layer addresses named **targets** and is not bound to one cluster context. | `Sandbox.open_terminal(target, tab)` in simulator-design.md §7. |
| Accounts | **Multi-user from the MVP.** No single-user/local mode. OIDC/OAuth, `User`, session ownership, quotas in the base architecture. | Postgres and auth move into P2. `kops lab` stays a developer prototype. |
| Docs attribution | Copied or embedded Kubernetes docs keep CC BY 4.0 attribution; a plain link to kubernetes.io needs none. In Mock Exam, allowed docs follow the Linux Foundation's list at the time the profile is created. | Docs mirror UI carries attribution; licence of every other source is checked. |
| Strict Exam Mode | Mirrors the official environment as published at profile creation; tools are never removed to make it harder. Tools managed as a **versioned Environment Profile**. | `vim`, `jq`, `helm` are excluded from the strict profile until confirmed from an official source; included in the practice profile. |
| Open consequence | Multi-user does not make DockerProvider safe for untrusted users. | Decision needed: invited users only (allow-list) for the MVP, or VmProvider first. |

## 2026-10-02 — Review round 5 (sandbox, auth, docs)

| Topic | Outcome | Consequence |
|---|---|---|
| Accounts | Ordinary multi-user platform: create account, login. No invite-only and no allow-list. Keycloak bundled; KOPS depends only on OIDC so the IdP can change. | Abuse controls from day one: email verification, rate limits, quotas, idle cleanup. |
| Sandbox | **KubeVirt.** `KOPS Platform → KubeVirt → VM(s) per session → kubeadm cluster`. `kind`/Docker only for development and CI. | **Supersedes** D-2 (B2 engine) in backend-design.md: Incus is no longer the choice. DockerProvider is no longer a user-facing option. Scenarios validated on kind must be re-validated on VMs. |
| Deployment dependency | Worker nodes need `/dev/kvm` (nested virtualization on OpenStack). Not yet checked. | Spike S-V0. Data point: `sre-control` exposes `/dev/kvm`, VT-x and nested=Y. |
| Docs in Mock Exam | CKA/CKAD: Kubernetes Documentation (search allowed, no external results), Kubernetes Blog, Helm Documentation, task Quick Reference links; CKA also Gateway API. CKS has a separate list and never appears in CKA/CKAD. | Per-profile docs mirror with local search; licence of non-Kubernetes sources still to be checked. |
| Editor / tools | LF lists on designated hosts: kubectl + `k`, bash completion, yq, curl, wget, man. LF pages do not name vim; they say to press `i` for insert mode. | Strict profile: vi-style editor included (inferred), `jq` excluded, `helm` only where a task requires it. Strict profile has no editor tab. |
| S-V0 partial result | Both lab workers (`sre-worker01` 192.168.28.226, `sre-worker02` 192.168.28.130) expose `/dev/kvm` with `kvm_intel nested=Y`, 16 vCPU and 31 GiB RAM each. | Nested virtualization is not a blocker. KubeVirt install state, CSI, CNI and spare capacity still unchecked. Capacity is small (about 4 concurrent sessions, estimate), so admission control is mandatory. |

## 2026-10-02 — Review round 6 (editor, licences, lab cluster check)

| Topic | Outcome | Consequence |
|---|---|---|
| Editor | **vim.** | In the strict profile. The strict profile still has no editor tab. |
| Docs licences | Use the same sources the Linux Foundation permits. Checked: Kubernetes docs/blog CC BY 4.0; Helm docs MIT (© 2017 Microsoft); Gateway API Apache-2.0. | Mirror ships the notices; third-party assets and trademark guidance not checked. |
| Lab cluster (read-only check) | Kubernetes **v1.28.15**, 3 nodes, Cilium, Longhorn, MetalLB. **No KubeVirt, no CDI, no CSI snapshot CRDs.** Shared with about 24 namespaces of other lab services. Workers: 26 % CPU requested, 14–23 % memory requested. | KubeVirt is **not** ready there. KubeVirt's support matrix (as read) does not list Kubernetes 1.28. Decision needed on where KubeVirt runs (simulator-design.md §13). |
| Host cluster candidate | `sre-test1`: Kubernetes 1.32.8, 3 nodes, all with `/dev/kvm` and nested=Y, nearly idle. No KubeVirt/CDI/CSI snapshots. **CNI is Flannel (no NetworkPolicy enforcement).** Multus present. | Proposed KubeVirt host for the S-V0 spike. Open: KubeVirt version for 1.32 or upgrade to 1.34+, session isolation without NetworkPolicy, and permission to dedicate it. |
| Other clusters (read-only check) | Five CAPI/OpenStack workload clusters, all Kubernetes 1.32.8, Flannel + Multus, Longhorn, nearly idle, Karmada members. `ramp-demo` exists only on `workload01` (2 pods) and `workload02` (7 pods); `sre-test1` and `sre-test2` have no RAMP namespace. `/dev/kvm` verified only on `sre-test1`. | Recommendation: a new dedicated cluster (Kubernetes 1.34+, policy-enforcing CNI, not a Karmada member) as the KubeVirt host. `sre-test2` with KubeVirt 1.7 only as an interim spike. Owner decides. |

## 2026-10-02 — Host cluster built (direct kubeadm, no Cluster API)

| Item | Result |
|---|---|
| Cluster | Kubernetes **v1.35.9**, kubeadm, containerd 2.2.1, 3 OpenStack VMs in project `workflow-prj` on the `provider` network: `kops-control-plane-1` (192.168.28.124, m1.large 4 vCPU/8 GiB), `kops-worker-1` (.139) and `kops-worker-2` (.200) (m1.xlarge 8 vCPU/16 GiB). Image `Ubuntu2204`, keypair `workflow-prj`, security group `default`. |
| CNI | **Cilium 1.20.2** (ipam kubernetes, kube-proxy kept). NetworkPolicy enforcement verified across nodes (allowed client reached the server, other client blocked). |
| `/dev/kvm` | Present on all three VMs, `kvm_intel nested=Y`. |
| Not a Karmada member, not managed by Nephio or Cluster API. | Admin kubeconfig: `/home/ubuntu/kops-k8s.kubeconfig` (mode 600). |
| Capacity caveat | OpenStack RAM is almost fully allocated (about 59 GiB free) and compute04 is down; flavors were chosen to fit that. About 2 KubeVirt sessions fit on the two workers (estimate). |
| Next | KubeVirt 1.8/1.9 (supports Kubernetes 1.35), CDI, a CSI or hostPath storage for VM disks, then spikes S-V1 to S-V3. |

## 2026-10-03 — KubeVirt, CDI and Longhorn on the `kops` cluster

| Item | Result |
|---|---|
| Installed | Longhorn 1.13.0 (replicas 2, instance-manager CPU 5 %), KubeVirt v1.9.0, CDI v1.66.1, `virtctl` v1.9.0 on the control plane. Prerequisites on workers: open-iscsi, nfs-common, iscsi_tcp and dm_crypt modules, multipath blacklist for `sd*`. |
| VM tests | cirros VM from containerDisk boots with KVM (42 s to ssh port); CDI import 168 s; CDI clone 139 s; boot from clone 44 s. See simulator-design.md §11. |
| Repo copy | `/home/ubuntu/kops` copied to `kops-control-plane-1` (798 files, sha256 verified; no `.git`, `.venv`, results or credentials). |
| Open | Install the CSI snapshot controller and re-measure clone time; decide golden-image delivery (containerDisk vs PVC); measure a kubeadm node VM (boot to Ready); capacity with real session VMs (RAM is the limit). |

## 2026-10-03 — Sandbox spike S-V1 results

| Item | Result |
|---|---|
| Clone strategy | CSI snapshot controller v8.6.0 + `VolumeSnapshotClass` `longhorn-snap`; StorageProfile `cloneStrategy: csi-clone` on `longhorn` and `longhorn-1r` (1 replica). Clone of a 10 GiB golden disk: 4.7 s. |
| Golden node image | PVC `golden/builder-disk` (Ubuntu 22.04, kubeadm 1.35.9, Calico v3.33.0 preloaded). |
| Session simulation | 2-node nested kubeadm cluster Ready in 248 s from clone request; about 4.7 GiB host memory for the two VMs; teardown 47 s. Details in simulator-design.md §11. |
| Capacity | About 2 sessions on the two 16 GiB workers by requested memory unless overcommit is configured. |
| Next | S-V2: isolation by NetworkPolicy between sessions, gateway to base ssh path, verifier from outside the VMs. |

## 2026-10-03 — Sandbox spike S-V2 results

| Item | Result |
|---|---|
| Isolation | Default-deny NetworkPolicy per session namespace (Cilium) blocks session-to-session, host API, host nodes and internet from inside the VMs; own-namespace traffic works. |
| Gateway | Platform gateway pod reaches `role=base` on 22 and `role=node` on 6443 only. |
| Verifier | `kops-verifier` kubeconfig minted per session with `kubeadm kubeconfig user`, kept as a Secret outside the VMs; a verifier pod ran `kubectl` against the session cluster. |
| Finding | Default-deny also blocks `virtctl ssh`; terminals use gateway-pod ssh to `base`. Docs-mirror and DNS egress rules not yet tested. |
| Open | S-V3 (quota, orphan sweeper, 10 concurrent sessions), inner CNI choice, golden-image build robustness. |

## 2026-10-03 — Session time and reset options

| Item | Result |
|---|---|
| Question | A new session per task (248 s) is too slow; can one session reuse a cluster that is fully restored after every task? |
| Measured | Guest boot 24.5 s; the bottleneck is Longhorn volume attach after clone or restore (72 to 136 s); disk-level restore of a VM verified complete, 110 s per cycle; pod IP changes on every restart. |
| Proposal | Tiered reset per scenario: `reset: api` (reuse the cluster, delete scenario-created objects, verify a baseline digest) for object-level scenarios; `reset: vm` (snapshot restore, immutable containerDisk or warm spare cluster) for node-level scenarios. |
| Needs | Stable VM addressing for restart-based reset; measurement of API-level reset in a nested cluster; containerDisk golden image test. |
| Golden image | `golden/node-golden` (v2) is the current clone source; `builder-disk` (v1) was captured mid-reboot and should be deleted. |

## 2026-10-03 — containerDisk and API reset measurements

| Item | Result |
|---|---|
| containerDisk golden image | Built from `golden/node-golden` (qcow2 1.51 GiB, OCI image `localhost/kops/node-golden:v2` imported into containerd on both workers by `ctr`). |
| Cluster build | 109 to 114 s from request to a Ready 2-node cluster (was 248 s). VM to ssh about 41 to 46 s; kubeadm and Calico about 70 s. |
| Reboot / poweroff | Guest reboot keeps IP, files and cluster; guest poweroff or VMI loss changes the pod IP and discards the COW layer. |
| API-level reset | 12.5 s to digest equality in the nested cluster (222 objects), objects only. |
| Consequence | Stable IPs (Multus) are optional: needed only for pre-initialised cluster images. Reset by recreation works without them. |
| Left on the cluster | Image `localhost/kops/node-golden:v2` (about 1.5 GiB) on both workers; PVCs `golden/ubuntu-base`, `golden/builder-disk` (v1, to delete), `golden/node-golden` (v2). |

## 2026-10-03 — v0.1 built and deployed

| Item | Result |
|---|---|
| Scope | v0.1 = Practice + Playground + dashboard + accounts (Mock Exam, docs mirror, editor, node-level scenarios are later). |
| Built | `SandboxProvider` + `KubeVirtProvider`; FastAPI platform with OIDC (bundled Keycloak, self-registration), SQLite, sweeper, SSE, terminal WebSocket; static dashboard; API-level reset; `kops selftest-vm`; golden image v3 pipeline; Dockerfile and manifests; runbook `docs/operations.md`. |
| Deployed | `http://192.168.28.124:30800` (dashboard), `http://192.168.28.124:30880` (Keycloak). Admin by username: `bactp`. |
| Verified | End-to-end script `scripts/e2e-platform.py` passes (OIDC login, session in 125 s, terminal, CHECK PASS, restart in 36 s, delete). Browser: login redirect only. |
| Catalogue | Only scenarios validated on KubeVirt are offered (`catalog/available.txt`); validation of the single-node scenarios was running as two parallel Jobs at the time of writing. |
| Scenario reset | `catalog/reset-api.txt` holds the scenarios whose API reset restored the baseline digest after every trial; the others recreate the cluster. |
