# KOPS Platform — Practice Simulator Design (short)

- **Date:** 2026-10-03 (revised after the sandbox spikes and the lifecycle review)
- **Status:** PROPOSED. Nothing in §3–§12 is implemented except what §1 marks as existing.
- **Scope:** the KOPS platform is a **multi-user** web platform where people practise for CKA and CKAD (CKS later). Agent benchmarking is a second client of the same environment, built after the human experience works.
- **Decided architecture:** `KOPS Platform → KubeVirt → VM(s) per session → kubeadm Kubernetes cluster`. Self-service accounts through OIDC. `kind`/Docker is for internal development and CI only, not the sandbox architecture.

---

## 1. What exists and what this design changes

| Exists (Phase 1, kind-based) | Role from now on |
|---|---|
| Scenario format (task, fixtures, setup, criteria, hidden reference), lint, selftest | **Kept.** The scenario format is backend-neutral. |
| Verifier, trace, results, `kops lab` CLI, Tool Gateway | **Kept**, re-hosted behind `SandboxProvider`. |
| `kind` backend (`backend_kind.py`) | **Dev/CI only**: fast prefilter for scenarios and tests. Not the user-facing sandbox. |
| Scenarios validated on kind | Must be **re-validated on the VM sandbox** (§9): kind's CNI, storage class and node layout differ from a kubeadm cluster. |

**Principle.** Humans and agents work in the same kind of sandbox and are graded by the same verifier. What a person practises is what an agent is later measured on.

## 2. What the reference platforms do (and what we take)

| | Killercoda | killer.sh (official CKA/CKAD simulator) |
|---|---|---|
| Purpose | Step-based labs: learn and practise | Exam rehearsal |
| Sandbox | Disposable **VMs scheduled with KubeVirt** ("runs on containers, but interactive environments use virtual machines for stronger isolation", killercoda.com/about) | Remote Linux desktop (XFCE) modelled on the real exam |
| UI | Split view: instructions left, terminal right, optional in-browser IDE (Theia) | Full desktop with browser for docs |
| Grading | **CHECK** button per step, script exit code 0 = pass | Whole-session grade after a 2 h timer, score plus solutions |
| Content | Scenarios in GitHub repos (`index.json`, step markdown, `verify` / `background` / `foreground` scripts) | Fixed question set, 20–25 questions across several clusters |
| Limits | 1 h free, 4 h paid | 2 sessions, 36 h access each |

**We adopt:** the two-pane layout; per-task CHECK (practice) and end-of-session grading (mock exam); KubeVirt VMs as the sandbox; an offline docs browser.
**We do not adopt:** their scenario format (no negative control, no guards, no hidden reference) or their content (clean-room rule, see license-contamination-risk.md).
**Not verified:** Killercoda's internals beyond its public statements.

## 3. Session types

Every session belongs to one user.

| | **Practice** (build first) | **Mock Exam** (same engine) | **Playground** |
|---|---|---|---|
| Purpose | Learn one task at a time | Rehearse the real exam | Free exploration |
| Unit | One task at a time; the cluster is **reset between tasks** (`reset: api` or `vm`, see §3b) | A set of tasks (target 15–20) over several clusters; **provisioned once before the timer, kept until the end, graded at the end** | One cluster kept for the session |
| Clock | Optional soft timer | Hard timer (default 120 min) | TTL 1–2 h, extendable within quota |
| CHECK | Any time; each criterion with evidence | Not available; grade once at the end | None (not graded) |
| Hints / solution | 3 hints; solution marks the attempt *assisted* | Off; solutions after grading | n/a |
| Environment profile | `practice` | `strict` (mirrors the official environment, §10) | `practice` |
| Reset | "Restart task" resets the cluster (§3b) | **None during the exam** | Reset cluster, Stop, Delete |
| Topology | From the scenario | From the scenario | 1 control plane + 1 worker |
| Result | not started / attempted / solved / solved-assisted | Score report per domain: binary PASS per task plus weighted exam-style score (design-review.md §K.1) | None |

Rules: Practice and Mock Exam never reuse a playground or a previous session's sandbox. One active sandbox per user by default. The sandbox, scenarios and verifier are identical in every type; only policy differs.

## 3b. Lifecycle and reset policy

**The exam session, not the question, is the unit of isolation.** A question only maps to a target (host, cluster, namespace) inside an environment that already exists. Measured costs that drive this (single runs, see §11): a new 2-node cluster takes about 110 s with `containerDisk` images (248 s with Longhorn clones); an API-level reset takes about 12 s; a disk restore takes about 110 s.

### Practice
Each scenario declares how its cluster returns to the initial state:

| `reset` | Mechanism | For | Guarantee |
|---|---|---|---|
| `api` | Reuse the cluster: delete what the scenario created, restore what it changed, then require a state digest equal to the baseline | Object-level scenarios that touch only their own namespace and uniquely named cluster-scoped objects | API objects of the listed kinds only |
| `vm` | Recreate the VMs from the golden image (about 110 s, reformed cluster) | Node-level or control-plane scenarios, and any scenario that touches `kube-system`, nodes or shared cluster-scoped state | Complete (the image is immutable) |

"Next task" in the same session uses `api` when both the finished and the next scenario allow it, and otherwise waits for a `vm` reset. `selftest` must prove that the declared reset restores the baseline digest; a scenario that changes nodes but declares `api` is rejected by lint. Reset is started in the background as soon as a task ends, while the user reads the result.

### Mock Exam
```
Create exam session → provision the whole environment → wait until ALL hosts and clusters are Ready
   → START TIMER → Q1 … Q20 (no provisioning or reset between questions) → final grading → destroy
```
- **State machine:** `PROVISIONING → READY → RUNNING → SUBMITTED → GRADING → DESTROYED`. The timer never runs before `READY`. If the platform itself blocks the candidate (a VM or the access path is down, not something the candidate broke) the session goes `RUNNING → INFRA_BLOCKED → RUNNING` and the timer is paused. Only platform-owned health is checked; a kubelet or control plane the candidate broke stays the candidate's problem and the timer keeps running.
- **Topology:** `base` plus a *general* cluster for object-level questions, plus a pool of *destructive* clusters for questions that can break nodes or the control plane.
- **`resetDomain`:** each scenario names `general` or `destructive`. In the general cluster every question gets its own namespace and uniquely named cluster-scoped objects (lint enforces it).
- **Double buffering of the destructive pool (`warmSlots: 2`):** the candidate works in slot A; when the question ends the slot is marked dirty and recreated in the background while the next destructive question uses slot B. Reset time stays off the critical path.
- **Durability rule:** a VM that holds exam state the candidate must not lose (`base`, the general cluster) should not depend on node-local ephemeral storage. A destructive slot may use `containerDisk` because it is recreated anyway. A guest `reboot` keeps changes; a guest `poweroff` or a lost node discards an ephemeral layer.
- **Capacity:** about 16 GiB of requested memory for one full exam (general 2 VMs, two destructive slots of 2 VMs, `base`) on the current two 16 GiB workers; more with memory overcommit or larger workers.

### Playground
One cluster kept for the session (1 control plane, 1 worker), TTL with extension, Reset, Stop, Delete. Never graded.

## 4. Interface

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ KOPS   CKA ▸ Troubleshooting ▸ Service endpoints   Practice  ⏱ 00:12   user ▾ │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ [Tasks] [Task] [Hints]        │ [Terminal 1] [Terminal 2] [+]  [Editor] [Docs]│
│                               │                                              │
│ Task list (filter by profile, │ candidate@base:~$ ssh node01                  │
│ domain, difficulty, status)   │                                              │
│  ✓ Service endpoints   (2)    │  Each tab is a shell on the session's base    │
│  ○ Rollback a Deployment (2)  │  VM; the candidate reaches designated hosts   │
│  ○ ConfigMap env vars  (1)    │  with ssh, as in the exam.                    │
│                               │  Editor: code-server (practice profile only). │
│ Selected task: description,   │  Docs: offline mirror with local search.      │
│ objectives, constraints       │                                              │
│ [ CHECK ] [Hint] [Solution]   │                                              │
│ [Restart task]                │                                              │
└───────────────────────────────┴──────────────────────────────────────────────┘
```

The left pane keeps the task visible (unlike the CLI prototype). All terminal tabs share the base VM's file system. The **Editor tab exists only if the active profile enables it**: the real exam offers a terminal and a browser, not an IDE, so the strict profile disables it (§10).

## 5. Architecture

```
 Browser (SPA) ─OIDC─▶ Keycloak (bundled; any OIDC IdP can replace it)
   │ task pane         │ token
   │ xterm.js          ▼
   │ editor, docs ──▶ API server ──▶ Registry (scenarios, lint, digest)
   ▼                    │  ├────────▶ Session manager ──▶ KubeVirtProvider ──┐
 Agent Gateway (later)  │  ├────────▶ Verifier                               │ Kubernetes API of the host cluster
 (service identity)     │  └────────▶ Postgres (users, sessions, quota,      ▼
                        │              progress, results)        namespace kops-s-<session>  (owner label,
                        │                                          ResourceQuota, default-deny NetworkPolicy)
                        └── terminal/editor/docs gateway ─────────▶   VM base  ── ssh ──▶ VM cp-1, node-1 (kubeadm)
                                                                       [VMs for further clusters in a Mock Exam]
```

| Component | Responsibility |
|---|---|
| **Auth** | OIDC/OAuth2 only. The platform depends on the OIDC protocol, not on Keycloak, so the IdP can change. Self-registration (create account, then login) is provided by the bundled Keycloak. Roles: `user`, `admin`, plus a `service` identity for agent runs. |
| **API server** | Catalog, sessions, terminal and editor proxying, CHECK, hints, solution, progress. Python (FastAPI) reusing the `kops` package. Every endpoint is authorised against session ownership. |
| **Session manager** | Lifecycle (§6), ownership, quota, timers, idle timeout, orphan sweeper. |
| **KubeVirtProvider** | Creates and destroys the session namespace and its `VirtualMachine` resources (§7). |
| **Verifier** | Existing engine, running **outside** the VMs with credentials that are not stored in them. |
| **Docs mirror** | Platform-side static site per environment profile, with local search, reachable from sandboxes (§10). |
| **Store** | Postgres. |

**Platform host.** The platform runs on a Kubernetes cluster that has KubeVirt installed (the lab's own infrastructure). The user-facing session is VMs, not pods.

## 6. Session lifecycle and ownership

```
REQUESTED → PROVISIONING → SETUP → CONFIRMED → ACTIVE ⇄ CHECKING → ENDED → DESTROYED
                 │            │          │                                   ▲
                 └────────────┴──────────┴──── INVALID (infra fault, retry) ─┘
```

- Every session has `owner_user_id`, `type`, `profile` (environment profile id and version). Every Kubernetes resource of the session carries session and owner labels.
- Only the owner and admins can open terminals, CHECK, read results or delete the session.
- SETUP runs the scenario's setup against the session's cluster; CONFIRMED means the negative control passed.
- DESTROYED always follows ENDED, TTL expiry or idle timeout (delete the namespace). Practice and Mock Exam sandboxes are never reused.
- The session record keeps: user, scenario id and revision, digest, seed, type, profile id and version, timestamps, every CHECK, hints and solution used, outcome, environment fingerprint (golden image digests, Kubernetes version).

## 7. Sandbox on KubeVirt

Per session, in its own namespace (`kops-s-<id>`):

| Resource | Purpose |
|---|---|
| `VirtualMachine` **base** | The candidate's entry host (hostname `base`, as in the exam). Tools from the environment profile. Does not run the cluster. |
| `VirtualMachine`s **cp-1, node-1, …** | A kubeadm cluster built from golden images, one set per cluster in the scenario. Designated hosts reached with `ssh <node>`. |
| ResourceQuota, default-deny NetworkPolicy | Limits per session; VMs can reach each other and the docs mirror, nothing else (no internet, no host cluster API, no other sessions). |

```python
class SandboxProvider(Protocol):
    def provision(self, spec: SandboxSpec, owner: UserId) -> Sandbox: ...
    def health(self, sb: Sandbox) -> Health: ...
    def destroy(self, sb: Sandbox) -> None: ...
    def list_owned(self) -> list[SandboxRef]: ...             # orphan sweeper

class Sandbox(Protocol):
    def targets(self) -> list[Target]: ...                     # base, cp-1, node-1, ...
    def open_terminal(self, target: str, tab: str) -> PtyStream: ...
    def exec(self, argv, *, as_: Literal["candidate", "verifier"], target: str = "base") -> ExecResult: ...
    def kubeconfig(self, who: Literal["candidate", "verifier"]) -> Path: ...
    def endpoints(self) -> dict[str, str]: ...                 # editor, docs
    def fingerprint(self) -> dict: ...
    def state_digest(self) -> str: ...
```

Terminals address named **targets**, so the model workstation → ssh → designated host is part of the interface, not an afterthought.

| Provider | Role |
|---|---|
| **KubeVirtProvider** | The sandbox architecture. Used by the platform. |
| **KindProvider** (existing Phase 1 backend, behind the same interface) | Internal development and CI only. Not exposed to users. |

**Disks.** Session VMs boot from `containerDisk` images (read-only golden image plus a per-VMI copy-on-write layer, discarded when the VMI ends). Golden images are OCI images; until a registry exists they are imported into containerd on each worker. Longhorn is kept for persistent data (the platform database, and later any VM that must survive a node restart). Stable VM IPs are not needed for reset by recreation, because the cluster is re-formed after every recreation; they would only be needed to ship pre-initialised clusters (optional Multus optimisation, not built).

**Quotas:** per user, active sandboxes (default 1), maximum session length, maximum extensions; global concurrency from cluster capacity. A request over quota is refused with a clear message.

**Public self-registration implies abuse controls from day one:** email verification, rate limiting on session creation, per-user quota, global capacity limit, and automatic cleanup of idle or expired sessions.

### Unverified assumptions (spikes, §11)
- KubeVirt needs worker nodes with hardware virtualization. **Checked 2026-10-02:** `sre-worker01` (192.168.28.226), `sre-worker02` (192.168.28.130) and `sre-control` all expose `/dev/kvm`, VT-x and `kvm_intel nested=Y` (Ubuntu 22.04.4, kernel 5.15.0-117, 16 vCPU and 31 GiB each; the workers are KVM guests, so session VMs would be nested). This removes the nested-virtualization blocker.
- **Lab cluster state (read-only check, 2026-10-02):**
  - Kubernetes **v1.28.15**, 3 nodes (1 control plane with NoSchedule taint, 2 workers), containerd 1.7.13.
  - **KubeVirt and CDI are not installed.** No snapshot-controller CRDs either (`VolumeSnapshotClass` is absent).
  - CNI: **Cilium** (NetworkPolicy enforcement available). Storage: **Longhorn** CSI (default class, RWO, Immediate binding; its own `snapshots.longhorn.io` CRDs exist). LoadBalancer: MetalLB. No Ingress controller. No metrics-server.
  - The cluster is **shared**: about 24 namespaces of other work (Argo CD, Flux, Gitea, Karmada, kagent, LibreChat, Longhorn, MinIO, Nephio/Porch, Cluster API with the OpenStack provider, sregym-runner, …).
  - Requested resources on the workers: worker01 26 % CPU / 23 % memory, worker02 26 % CPU / 14 % memory (requests, not usage; limits are overcommitted at 109–113 % CPU).
- **KubeVirt compatibility (needs confirmation):** the KubeVirt support matrix (`kubevirt/sig-release`, read through a fetch tool) lists Kubernetes 1.31–1.36 and shows KubeVirt 1.9 supporting 1.34–1.36; Kubernetes 1.28 does not appear. If that holds, the lab cluster at 1.28.15 is outside the maintained window of current KubeVirt, and hosting KubeVirt there means either an old unsupported KubeVirt release or upgrading the cluster. A dedicated host cluster at Kubernetes 1.34+ is the cleaner option (the lab already runs Cluster API with the OpenStack provider).
- **Shared-cluster risk:** user VMs for self-registered users would run beside Argo CD, Gitea, Karmada and others. A VM escape or a noisy session would hit lab services. Dedicated nodes (labels and taints) are the minimum; a dedicated cluster is better.
- **Candidate host cluster `sre-test1` (read-only check, 2026-10-02; kubeconfig `~/sre-test1.kubeconfig`):**
  - Kubernetes **v1.32.8** (created with Cluster API on OpenStack), 3 nodes: 1 control plane (no taint) and 2 workers, containerd 1.7.25, Ubuntu 22.04.5.
  - All three nodes (floating IPs 192.168.28.184, .202, .191) expose `/dev/kvm`, VT-x and `kvm_intel nested=Y`; 16 vCPU and 31 GiB RAM each (about 27 GiB free on each); about 142 GiB free disk each.
  - **Nearly idle:** requests 14–18 % CPU and 1–2 % memory per node; usage 1–4 % CPU and 13–18 % memory. Existing workloads: Argo CD, Flux, Longhorn, OpenEBS, MetalLB, metrics-server, one `sregym` namespace (do not touch), a `pod-prepull` namespace.
  - **KubeVirt, CDI and CSI snapshot CRDs are not installed.** Multus is installed (`NetworkAttachmentDefinition` CRD exists). Storage classes: Longhorn (default), OpenEBS hostpath and device. An `nginx` IngressClass exists, but no ingress-nginx namespace was seen.
  - **CNI is Flannel. Flannel does not enforce NetworkPolicy**, so a default-deny NetworkPolicy per session namespace would not isolate anything. Session isolation needs a different mechanism (a policy-capable CNI added alongside, or isolation through per-session Multus networks), and must be proven in spike S-V2.
  - Rough capacity (estimate, not measured): about 27 GiB free on each of 3 nodes. A session of three 2-vCPU / 3–4 GiB VMs needs about 9–12 GiB, so roughly 7 concurrent sessions if the control-plane node is also used, about 4–5 on the two workers. Still small for open registration; admission control stays mandatory.
  - **KubeVirt support for Kubernetes 1.32.** The support matrix (read through a fetch tool) marks Kubernetes 1.32 as EOL upstream, and shows KubeVirt 1.5, 1.6 and 1.7 as having supported it; KubeVirt 1.8 and 1.9 start at 1.34 and 1.35 respectively. Whether those KubeVirt releases are still maintained is not stated. Options: run an older KubeVirt (1.7 is the newest listed for 1.32) for the spike, or upgrade `sre-test1` to Kubernetes 1.34+ first.
- **All other clusters (read-only check, 2026-10-02).** Five workload clusters are managed by Cluster API on OpenStack from the 1.28 management cluster, and all five are members of Karmada (push mode):

  | Cluster | Nodes | Version | CNI | Other notes |
  |---|---|---|---|---|
  | `sre-test1` | 1 CP + 2 workers | 1.32.8 | Flannel + Multus | `sregym`, `openebs`; **no RAMP namespace** found |
  | `sre-test2` | 1 CP + 2 workers | 1.32.8 | Flannel + Multus | Same as `sre-test1` without `openebs`; **no RAMP namespace** found; cleanest of the five |
  | `workload01` | 1 CP + 1 worker | 1.32.8 | Flannel + Multus | **`ramp-demo` (2 pods)**, Velero |
  | `workload02` | 1 CP + 1 worker | 1.32.8 | Flannel + Multus | **`ramp-demo` (7 pods)**, Velero |
  | `workload03` | 1 CP + 1 worker | 1.32.8 | Flannel + Multus | Velero; no `ramp-demo` |
  | management (`mgmt`) | 1 CP + 2 workers | 1.28.15 | Cilium | Cluster API, Karmada, Nephio, Gitea, kagent, LibreChat, …; the shared cluster described above |

  All five workload clusters are nearly idle, none has KubeVirt or CSI snapshot CRDs, and all use Flannel (no NetworkPolicy enforcement). Their nodes' `/dev/kvm` was verified only for `sre-test1`; the `10.6.0.x` addresses of the others are not reachable from `sre-control`, so the rest are unverified. Reading `/dev/kvm` through Kubernetes would need a privileged pod, which changes the cluster and was not done.
  - **Karmada coupling.** Because all five are Karmada members, workloads can be propagated onto them from the hub. A cluster that runs untrusted user VMs should not be a Karmada member.
- Golden-image provisioning time. Two options: boot pre-initialised disks (needs identical internal addressing in every session, for example a per-session secondary network with fixed IPs), or run `kubeadm init/join` at provisioning time with preloaded images. Neither is measured.
- Capacity: a session is at least 3 VMs. Rough estimate, not measured: with about 25 GiB free RAM and 16 vCPU on each of two workers, a session of three 2-vCPU / 3–4 GiB VMs (about 9–12 GiB) allows roughly 4 concurrent sessions across both workers, before KubeVirt overhead. That is far below what open self-registration could generate, so session admission control (queue or refuse) is required, and more workers will be needed for any real user base.
- Storage: KubeVirt needs a CSI driver that supports cloning or snapshots for fast disk creation.
- The lab CNI must enforce NetworkPolicy for session isolation.

## 8. Deployment

| | Production | Dev / CI |
|---|---|---|
| Host | Lab Kubernetes cluster with KubeVirt, Keycloak, Postgres, API server, docs mirror | Docker Compose with `KindProvider` and a stub IdP |
| Users | Self-registered | Developers |
| Sandbox | KubeVirt VMs per session | kind clusters (Phase 1) |
| Purpose | Real use | Fast scenario prefilter and tests |

Common requirements: images preloaded or served by a local registry, no secrets inside a sandbox, resource limits per session, TTL, per-owner labels, orphan sweeper.

## 9. Content model

```
scenarios/<id>/
  scenario.yaml  task.md  setup/  fixtures/  verify/criteria.yaml  metadata/        # existing
  reference/solution.sh  reference/wrong-*.sh                                        # existing, hidden from candidates
  reference/explanation.md   # root cause, approach, commands, what the verifier checks
  reference/hints.md         # 3 progressive hints
```

Optional per-scenario additions: `tools_required` (for example `helm`, installed on the designated host because the task needs it) and `docs_extra` (links an exam task would supply in its Quick Reference).

**Validation across backends.** A scenario passes `selftest` on kind first (cheap). It becomes `validated` for users only after `selftest` also passes on the KubeVirt sandbox. The scenarios written so far are kind-validated only.

## 10. Environment profiles

Tools, aliases, shell setup, editor, documentation sources and rules of a session come from a **versioned Environment Profile**, not from code.

```yaml
# profiles/cka-strict-v1.35-<date>.yaml  (illustrative)
id: cka-strict
version: 1.35-<date>
kind: strict                              # strict | practice
sources: [https://docs.linuxfoundation.org/tc-docs/certification/tips-cka-and-ckad,
          https://docs.linuxfoundation.org/tc-docs/certification/certification-resources-allowed]
retrieved: <date>
kubernetes_version: "1.35"
hosts: {base: {user: candidate}, designated: ssh}
tools: [kubectl, bash, bash-completion, yq, curl, wget, man, ssh, vim]   # vim: owner decision, see below
aliases: {k: kubectl}
ui: {editor_tab: false, docs_tab: true}
docs: [kubernetes.io/docs, kubernetes.io/blog, helm.sh/docs, gateway-api.sigs.k8s.io]   # CKA; CKAD has no Gateway API
rules: {hints: false, check: false, restart: false, timer_minutes: 120}
```

- **Strict** mirrors the official environment as the Linux Foundation publishes it when the profile is created. It is not a harder variant: tools are neither removed to make it difficult nor added for convenience. A new official environment means a new profile version. **Practice** may add tools and the editor tab, and says so in the UI.
- **Verified (Linux Foundation pages):**
  - Designated SSH hosts have "kubectl with k alias and Bash autocompletion, yq for YAML processing, curl and wget for testing web services, man and man pages".
  - Tasks run on designated hosts reached with `ssh <nodename>`; the base node (hostname `base`) must not be rebooted.
  - The instructions tell candidates to press `i` for insert mode, so the environment has a vi-style editor. The pages **do not name** vim, nor list `jq`, `tmux` or `helm` among the pre-installed tools.
- **Strict profile decisions from that:** the editor is **vim** (owner decision 2026-10-02; the official pages only imply a vi-style editor); exclude `jq`; `helm` is provided only on designated hosts of tasks that need it (`tools_required`), because Helm documentation is an allowed source, but the binary is not listed.
- **Documentation sources allowed by the Linux Foundation:**
  - **CKA and CKAD:** Kubernetes Documentation (`kubernetes.io/docs`; using the site's search is allowed, opening external search results is not), Kubernetes Blog (`kubernetes.io/blog`), Helm Documentation (`helm.sh/docs`), and task-specific links in the Quick Reference.
  - **CKA only:** Gateway API Documentation (`gateway-api.sigs.k8s.io`).
  - **CKS has a separate list** (Falco, bom, etcd, NGINX Ingress Controller, Cilium, Istio, plus the Kubernetes sources). Those never appear in CKA or CKAD profiles.
- **Mirror requirements:** each profile's mirror contains exactly its list (plus the scenario's `docs_extra`), with local search so that no external search is needed, and the version pinned. Copied Kubernetes documentation keeps CC BY 4.0 attribution in the UI. Licences checked 2026-10-02 from the source repositories' LICENSE files:
  - Kubernetes documentation and blog (`kubernetes/website`): **CC BY 4.0**. Keep creator identification, copyright notice, licence notice and a note of any modification.
  - Helm documentation (`helm/helm-www`): **MIT**, Copyright (c) 2017 Microsoft Corporation. Keep the copyright and permission notice.
  - Gateway API (`kubernetes-sigs/gateway-api`, which contains the documentation site): **Apache-2.0**. Ship the licence text and attribution.
  - All three permit mirroring with those notices. Not checked: third-party images or assets inside the sites, and trademark guidance (do not imply endorsement). Record the result in the profile (`licence_checked`). Decision (owner): use the same sources the Linux Foundation permits.
- The profile id and version are recorded in every session and result.

## 11. Spikes before building the platform (the critical path)

| Spike | Question | Done when |
|---|---|---|
| **S-V0 Infrastructure** | Does the lab cluster expose `/dev/kvm` on its worker nodes (nested virtualization on OpenStack)? KubeVirt version compatibility, free CPU and RAM, CSI with clone/snapshot, CNI with NetworkPolicy | A VM boots on a worker node and answers ssh |
| **S-V1 Golden images** | Build base and node images with kubeadm 1.35; choose pre-initialised disks vs. init at provisioning; measure time to a Ready cluster; measure resources per session | A 3-VM cluster is Ready with a recorded time |
| **S-V2 Access path** | Browser terminal to `base`, ssh hop to nodes, docs mirror reachable, everything else denied, verifier reaching the cluster from outside the VMs with credentials not stored inside | A scenario setup + CHECK works end to end on a VM cluster |
| **S-V3 Operations** | Ownership labels, quota, orphan sweeper, destroy time, behaviour under 10 concurrent sessions | Numbers recorded |

### Spike results (2026-10-03, cluster `kops` built with kubeadm)

Host cluster: Kubernetes 1.35.9, Cilium 1.20.2 (NetworkPolicy enforcement verified across nodes), Longhorn 1.13.0 (2 replicas, 2 workers), KubeVirt v1.9.0, CDI v1.66.1; 3 OpenStack VMs (4 vCPU/8 GiB control plane, two 8 vCPU/16 GiB workers). Nested KVM works: the workers advertise `devices.kubevirt.io/kvm`, and VMs run without emulation.

Single runs, not repeated; the first run includes image pulls.

| Measurement | Result |
|---|---|
| VM from a `containerDisk` (cirros, 256 MiB RAM), create → guest answers on tcp/22 | 42 s |
| CDI import of a cirros qcow2 into a 1 GiB Longhorn PVC | 168 s |
| CDI clone of that PVC into a new 1 GiB PVC (no CSI snapshot controller installed, so host-assisted clone) | 139 s |
| VM boot from the cloned PVC, create → guest answers on tcp/22 | 44 s |

Reading: root disks cloned from a golden PVC cost minutes per disk with this storage setup, which is too slow for three or more disks per session. A `containerDisk` needs no PVC and boots in tens of seconds, and session disks are disposable anyway. Candidate design for S-V1: golden images shipped as containerDisk images in a local registry. Open: whether Longhorn smart clone through the CSI snapshot controller (not installed) is fast enough, and the boot time of a kubeadm node image (much heavier than cirros).

### Spike results, continued (2026-10-03): clone strategy and a nested kubeadm cluster

Single runs, not repeated. Same host cluster as above (workers 8 vCPU / 16 GiB, nested KVM).

**CDI clone strategy on Longhorn** (1 GiB PVC): `copy` 139 s, `snapshot` 4.5 to 8.6 s, `csi-clone` 2.4 to 4.4 s (after installing the CSI snapshot controller v8.6.0 and a `VolumeSnapshotClass`; the StorageProfile `cloneStrategy` was set to `csi-clone`). Session StorageClass `longhorn-1r` uses one replica.

**Golden image as a PVC** (Ubuntu 22.04 cloud image, 10 GiB disk, containerd 2.x, kubeadm/kubelet/kubectl 1.35.9, kubeadm and Calico v3.33.0 images preloaded, 3.8 GiB used): one-time import 453 s, build 4 + 6.5 min; cloning it into another namespace takes 4.5 to 4.7 s per disk.

**One simulated session: base-less 2-node kubeadm cluster from two clones (1 control plane 2 vCPU / 4 GiB, 1 worker 2 vCPU / 3 GiB):**

| Stage | Time |
|---|---|
| Clone both disks (cross-namespace) | 4.7 s |
| Control-plane VM boot to ssh | 115.6 s |
| `kubeadm init` + Calico apply | 20.7 s |
| Worker VM boot to ssh | 57.0 s |
| Join to both nodes `Ready` | 46.8 s |
| **Request to a Ready 2-node cluster** | **248 s** |
| Teardown (namespace, 2 VMs, 2 PVCs) | 47 s |

Steady-state memory (30 s after Ready): control-plane VM 906 MiB used inside the guest, 2829 MiB measured on the host (guest page cache included); worker 344 MiB used inside, 1896 MiB on the host. Together about 4.7 GiB on the host for the two VMs, against 7 GiB requested. A third VM (`base`) would add roughly 1 to 1.5 GiB. This is well below the 9 to 12 GiB per session assumed earlier, but scheduling uses the requested memory, so with the two 16 GiB workers (about 5 GiB already requested by Cilium, Longhorn and KubeVirt on each) about 2 sessions fit unless memory overcommit is configured. The 248 s is long for a practice session; the golden image already removes the package installs, so what remains is VM boot and kubeadm, and pre-initialised disks (a cluster formed at build time) would cut it further.

Open issues found: the control-plane VM first boot (115 s) is twice the worker's (57 s); a golden build script bug (SIGPIPE under `set -e -o pipefail`) skipped the final cleanup once and was caught only by checking the log.

### Spike results, S-V2 (2026-10-03): isolation and access path

Setup: two session namespaces (`sa` with VMs `a-base` and `a-cp`, `sb` with `b-base`) plus a platform namespace `kops-gw` holding a gateway pod and a verifier pod. Session policies (standard Kubernetes NetworkPolicy, enforced by Cilium): default deny for ingress and egress; allow within the namespace; allow ingress from `kops-gw` to `role=base` on tcp/22 and to `role=node` on tcp/6443.

| Test | Result |
|---|---|
| From `b-base`: another session's base (22), its node (22, 6443) | all blocked |
| From `b-base`: the host cluster's API (ClusterIP 10.96.0.1:443), host nodes (192.168.28.124:6443, 192.168.28.139:22), the internet (1.1.1.1:443), the gateway pod | all blocked |
| From `a-base` to its own node: ssh port and cluster API | open (as intended) |
| From `a-base`: other session, host API, internet | blocked |
| Gateway to `a-base:22` and `b-base:22` | open |
| Gateway to `a-cp:22`, and to `a-base:6443` | blocked |
| Gateway to `a-cp:6443` | open (verifier path) |
| **Verifier**: kubeconfig for client `kops-verifier` minted on the node with `kubeadm kubeconfig user`, kept outside the VMs as a Secret in `kops-gw`; a pod in `kops-gw` ran `kubectl get nodes` against session A's API with it | worked |
| Three VMs in two namespaces booted concurrently, all reachable | 196 s |

Findings:
- A default-deny policy **also blocks `virtctl ssh`** (the API-server port-forward path): `dialing VM ... connection timed out`. Terminals therefore go through a gateway pod over ssh to `base` (allowed by policy). If the port-forward path is wanted, it needs an explicit allow rule for the node-side traffic (Cilium host entities), which standard NetworkPolicy cannot express; not tested.
- The test sessions had no DNS or documentation-mirror egress. A rule allowing the docs mirror (and DNS if guests need it) still has to be added and tested.
- Verifier identity is minted per session at setup and never copied into the VMs. A candidate with root on the node can still read the cluster CA key, so this is acceptable only for non-adversarial users (see §7 trust boundary).

Not yet done (S-V3): quotas, orphan sweeper, destroy behaviour under load, and 10 concurrent sessions. Inner CNI for session clusters (Calico used in the spike as a placeholder) is still a decision.

### Spike results, S-V1 follow-up (2026-10-03): where session time goes, and restoring in place

Single runs. Golden v2 = Ubuntu 22.04 with generic DHCP networking, snapd/lxd and unneeded services removed, GRUB without delay, shut down gracefully (12 s) before being used as a clone source.

**Where the time goes (one VM from a 10 GiB golden clone, 3.5 GiB used):**

| Stage | Time |
|---|---|
| CDI clone (csi-clone) reports `Succeeded` | 3.5 s |
| virt-launcher pod waits for the Longhorn volume to attach (`FailedAttachVolume` events, retried) | about 136 s in this run, 72 s in an earlier run |
| Guest boot (kernel 13.4 s + userspace 11.2 s) | 24.5 s |
| Create to ssh | 173.8 s |

So VM boot is not the bottleneck: the Longhorn attach of a freshly cloned or restored volume is. `kubeadm init/join` (about 70 s together) is the second cost.

**Restoring a VM in place from a disk snapshot (stopped VM, `VirtualMachineSnapshot` / `VirtualMachineRestore`):**

| Step | Time |
|---|---|
| Graceful stop | 12.2 s |
| Snapshot of the stopped VM | 2.4 s |
| Restore object complete | 2.6 s |
| Start after restore to ssh (new volume from snapshot, attach again) | 107.2 s |
| **Restore cycle (stopped dirty VM to usable restored VM)** | **109.9 s** |
| Plain restart of an unchanged disk, for comparison | 52.5 s |

Verification after restore: a deleted file was back (`marker=initial`), a new file and a new directory were gone. Disk-level restore returns the VM to the snapshot state completely.

**Two constraints found:**
1. **The VM's pod IP changes on every restart or restore** (10.244.2.150 to .63 to .41). A kubeadm cluster is bound to node IPs, so restart-based reset needs stable addressing (for example a per-session secondary network with static IPs through Multus, not installed) or re-initialising the cluster after each reset.
2. **Cloud-init's generated netplan is tied to the NIC MAC address.** A restarted VM gets a new MAC and loses its network (and waits 120 s for it). Golden v2 fixes this with generic DHCP matching `e*` and cloud-init network config disabled.

**Reset options for "every task starts clean" (design implication):**

| Option | Time | Guarantee | Status |
|---|---|---|---|
| A. Reuse the cluster; delete everything the scenario created and compare a state digest with the baseline (objects only) | est. seconds | API objects only; node files, kubelet and etcd changes not covered | not measured here |
| B. Restore all VM disks from a snapshot (parallel across VMs) | about 110 s measured | complete at disk level | needs stable IPs |
| C. Ephemeral `containerDisk` golden images, recreate VMs per reset | expected about 35 s (guest boot 25 s plus pod start), not measured | complete (image is immutable) | needs a registry or node-preloaded image, and stable IPs |
| D. Warm spare cluster, assigned instantly while a replacement is built in the background | near 0 s to the user | complete | costs memory for idle clusters (about 2 sessions fit now) |

A scenario would declare `reset: api` (option A, object-level scenarios) or `reset: vm` (B, C or D, node-level scenarios), and `selftest` would prove the declared reset restores the baseline digest.

### Spike results, containerDisk and reset (2026-10-03)

Golden v2 converted to a compressed qcow2 (1.51 GiB), wrapped by a small script as an OCI image with the file at `/disk/node-golden.qcow2`, and imported into containerd on both workers as `localhost/kops/node-golden:v2` (no registry, no new cluster components). VMs use `containerDisk` (the image is read-only, writes go to a per-VMI copy-on-write layer discarded when the VMI ends). Single runs; two clusters built, plus separate tests.

| Measurement | Result |
|---|---|
| VM create to ssh, cold (first start of the image on a node) | 40.9 s and 43.4 s (two VMs) |
| Delete both VMs | 19.6 s |
| Whole 2-node kubeadm cluster, request to both nodes Ready (cold / warm / third run) | **109.2 s / 113.4 s / 113.7 s** (was 248 s with Longhorn clones) |
| Of which `kubeadm init` + join + Calico to Ready | 66 to 69 s |
| Guest **reboot** of the control plane: pod IP, files, cluster | IP unchanged (10.244.2.244), marker kept, ssh back after 54 s, API and both nodes Ready after 72 s |
| Guest **poweroff** of a worker: KubeVirt starts a new VMI | new VMI reachable after 61 to 63 s, **pod IP changed, marker lost** (the COW layer is discarded) |
| API-level reset inside the nested cluster (222 baseline objects; scenario-style changes: 2 namespaces with deployment/service/configmap/role, a ClusterRole and binding, a StorageClass, a modified `kube-system/coredns` ConfigMap) | digest equal to baseline after **12.5 s** (deleted 5 top-level objects, restored 1) |
| Host memory (`memory.current` of virt-launcher), idle cluster | control plane 2588 MiB (guest 3 GiB, 766 MiB used), worker 677 MiB |

Corrections to earlier tests: a first run of the poweroff check failed because of a shell quoting error, and a first run of the API reset reported 8.2 s while 5 objects of the deleted namespaces were still being removed (digest not yet equal); both were re-run and the numbers above are from the re-runs.

Reading:
- Removing the Longhorn clone and attach path cuts the full cluster build from 248 s to about 110 s. VM boot to ssh is about 41 to 46 s; the rest is `kubeadm` and Calico (about 70 s).
- Because the cluster is re-formed after every recreation, **stable VM IPs are not required** for resets by recreation. They would be required only to ship pre-initialised clusters (which would remove most of the 70 s). A guest `reboot` keeps the pod IP; a guest `poweroff` or an infrastructure loss ends the VMI and loses its changes. Multus was not installed or tested.
- API-level reset restores API objects in about 12 s, but it cannot see node files, kubelet or etcd state, and the digest only covers the object kinds it lists.
- Not tested: node loss while a COW layer holds exam state, pre-initialised cluster images, shared RWX golden volumes, the effect of cross-node networking for a session (VMs landed on different workers in these runs and reached each other over the pod network).

### v0.1 implementation notes (2026-10-03)

Built and run on the lab cluster (Kubernetes 1.35.9, Cilium, Longhorn, KubeVirt 1.9.0, CDI 1.66.1). Measured on the deployed platform, single runs:

| Measurement | Result |
|---|---|
| Practice session from "Start" to ACTIVE (namespace, 2 VMs, kubeadm, Calico, local-path, probe pod, scenario setup and confirm) | 125 s |
| Restart of the task in the same session (API-level reset, then setup and confirm) | 36 s |
| Playground and Practice share the provisioning path | yes |
| `kops selftest-vm` trial of a scenario that PASSes, including setup and API reset | about 38 s; scenarios whose failing criteria wait for `settle` take about 100 s |

Defects found by running it for real, all fixed and covered by a test or a code note:
1. The orphan sweeper destroyed selftest sandboxes (namespace labelled managed, no session row). Sandboxes labelled `kops.io/exempt=true` are skipped by the sweeper.
2. The default-deny policy blocked the platform from ssh to the nodes (only 6443 was allowed). The platform is now allowed `22` and `6443` on `role=node`; candidates never hold its key.
3. Egress default-deny blocked DNS, so every lookup in a guest waited for a timeout (10 s for the VM's own hostname) and `kubeadm init` missed its deadline. DNS to kube-dns is allowed and the hostname is written to `/etc/hosts` by cloud-init. Known leak: DNS tunnelling. A later golden image should remove DNS from the guests instead.
4. The ssh config and `/etc/hosts` entries on `base` were written with literal backslash-n sequences, so `ssh cp-1` asked for host-key confirmation.
5. Keycloak and the platform could not write to their volumes (fsGroup).

Verified: the OIDC authorization-code flow with PKCE against the bundled Keycloak, the self-registration page, session quota (409), the terminal WebSocket (shell on `base`, ssh hop to the node, `kubectl` working), CHECK failing before and passing after a fix typed into the terminal, hints (404 when the scenario has none), solution, progress rules, restart back to the broken state, delete. Verified in a real browser only: the dashboard loads and redirects to the Keycloak sign-in page. **Not yet verified in a browser:** the dashboard after login (task pane, xterm rendering and resize, SSE), Playground, admin view.

## 12. Release plan

| Release | Content | Definition of done |
|---|---|---|
| P1 (done) | Pipeline on kind, selftest, CLI lab | |
| Spikes (done) | S-V0 to S-V2, containerDisk, reset measurements (§11) | Numbers recorded |
| **v0.1 (MVP)** | **Practice mode on the KubeVirt sandbox, Playground, dashboard, accounts.** `SandboxProvider` with `KubeVirtProvider`; golden image v3; platform API (FastAPI) and web dashboard; OIDC login with a bundled Keycloak (self-registration); owned sessions, one active session per user, TTL and orphan sweeper; task list, task pane, browser terminal on `base` with ssh to the cluster node, CHECK with evidence per criterion, three hints, solution (marks the attempt assisted), Next/Restart task with `reset: api` or `vm`, progress per scenario and domain; Playground (create, extend, reset, delete); admin view (users, sessions, capacity). Catalogue limited to the scenarios that pass `selftest` on the KubeVirt provider. SQLite. | Two users each complete a task in the browser without reaching each other's sandbox; no orphan resources after killing the platform pod; image and manifests reproducible from the repo |
| v0.2 | Mock Exam (provision-before-timer, state machine, general cluster plus destructive pool with double buffering, end grading, report, `resetDomain` lint); offline docs mirror with local search; code-server editor (practice profile); environment profile loader (practice and strict); Postgres; warm spare clusters for Practice; the remaining object-level scenarios re-validated on KubeVirt | A full mock exam on one host |
| v0.3 | Node-level and control-plane scenarios (kubelet, static pods, etcd, certificates) as `reset: vm` or destructive-pool scenarios; multi-cluster context switching; optional Multus stable IPs and pre-initialised cluster images; larger workers or more workers | CKA Troubleshooting and Cluster Architecture backlog designs runnable |
| v0.4 | Agent gateway on the session API; benchmark runs; human and agent graded on the same scenario | Same scenario graded for both |
| v1.0 | Hardened deployment (TLS, quotas, monitoring), open sign-up controls, CKS profiles and scenarios | Public beta |

**Deferred to later phases on purpose (not forgotten):** scenarios that change nodes, `kube-system` or shared cluster-scoped state (about 20 of the 60 current scenarios by a rough scan) need `resetDomain` and `reset: vm`; the remaining scenarios must each be re-validated on the KubeVirt provider (so far they are validated on kind only); backlog designs in `docs/scenario-backlog.md`; the scoring proposal in `docs/design-review.md` §K.1; documentation mirror and editor; Mock Exam.

### 12a. Warm pool (v0.1) and later scaling

Measured on the real sandbox: provisioning takes about 2 minutes (VM boot about 40 s, kubeadm about 50 s, baseline and setup about 25 s) and the hosts are not CPU or disk bound (average 20 to 25 percent CPU, no iowait), so more node resources would not shorten it. v0.1 therefore keeps a small fixed pool of ready clusters (`KOPS_WARM_POOL_SIZE`): a practice session adopts one (namespace relabelled, baseline already captured) and only runs the scenario setup (about 15 s). The API reset was also made cheaper (single-call state collection, force-deleted pods): 8 s measured. Later, when there are more users: size the pool from demand and free memory, per-scenario-family pools, pre-injected faults for the most used scenarios, refresh of old idle clusters, and the Mock Exam double buffer (§3b) built on the same adopt mechanism.

## 13. Decisions

**Resolved:**
0. Editor: **vim**. Documentation sources: the same ones the Linux Foundation permits; licences checked (§10).
1. Sandbox: `KOPS Platform → KubeVirt → VMs per session → kubeadm cluster`. `kind`/Docker only for development and CI.
2. Accounts: ordinary multi-user platform with self-registration; OIDC only; Keycloak bundled. No invite-only or allow-list requirement.
3. Docs sources for CKA/CKAD Mock Exam follow the Linux Foundation list (§10); CKS list is separate.
4. Editor tab: code-server in the practice profile; the strict profile follows the official environment (§10).
5. Terminal model: workstation (`base`) → ssh → designated host; terminals address named targets.
6. Playground, Practice and Mock Exam as in §3.
7. (2026-10-03) **Mock Exam: provision once before the timer, no reset between questions, session is the isolation unit**; destructive questions use a double-buffered pool of destructive clusters; Practice resets per scenario (`api` or `vm`) (§3b).
8. (2026-10-03) Session VMs boot from `containerDisk`; Longhorn is for persistent data; stable IPs are optional (§7).
9. (2026-10-03) First release is **v0.1 = Practice + Playground + dashboard + accounts** (§12); Mock Exam, docs mirror, editor and node-level scenarios are v0.2 and v0.3.
10. (2026-10-03) v0.1 uses SQLite behind SQLAlchemy; Postgres in v0.2.

**Open:**
1. ~~Do the lab's nodes provide `/dev/kvm`?~~ **Yes** where checked (§7). **Where does KubeVirt run?** Recommendation: a **new dedicated cluster**, not a Karmada member, created with the lab's Cluster API/OpenStack tooling on the same flavour and image family as the existing nodes (which expose `/dev/kvm` with nested virtualization), with: Kubernetes 1.34+ (KubeVirt 1.9 supports 1.34–1.36; the benchmark pins 1.35), a **NetworkPolicy-enforcing CNI** (Calico or Cilium) instead of Flannel, a CSI with clone/snapshot support, and enough workers (about 4 × 16 vCPU / 32 GiB gives roughly 10 concurrent sessions, estimate). Reasons: Kubernetes 1.32 is EOL and outside the range of maintained KubeVirt releases; Flannel cannot isolate sessions; Karmada can push workloads onto member clusters; and user VMs should not share a cluster with lab services. Fallback for an early spike only: `sre-test2` (cleanest existing cluster, no RAMP) with KubeVirt 1.7. Verify `/dev/kvm` on the new nodes after creation.
2. Whether `helm` is on the real designated hosts. The strict profile provides it only where a task requires it; correct the versioned profile if an official source says otherwise.
3. Mock Exam docs: offline mirror (reproducible, needs attribution and local search) or an allow-listed proxy to the live sites (higher fidelity, but internet-dependent and not reproducible)? The current decision is the offline mirror.
