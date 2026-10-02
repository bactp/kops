# KOPS Environment Backend Architecture — Proposal (G)

Status: **PROPOSED**. Numbers marked *(est.)* are engineering estimates that have **not** been measured yet. Spike S-1/S-2 (§8) exist to measure them before anything is frozen.

## 0. Summary

| Class | Name | Implementation (recommended) | Scope | Needed for |
|---|---|---|---|---|
| **A** | `kind` | kind, node image pinned by digest, add-on profile baked offline | Kubernetes API only | All of CKAD. Object-level CKA: workloads, scheduling, services, NetworkPolicy, RBAC, storage, HPA, Gateway/Ingress, Helm, Kustomize, CRDs |
| **B1** | `kind-node` | Same kind cluster, plus a KOPS-built **derived node image** (sshd, etcdctl/etcdutl) and node access through ssh from the workstation | Node **containers** that run real systemd, kubelet, containerd, crictl, kubeadm-generated PKI and static-pod control plane, stacked etcd | CKA troubleshooting of nodes and components: kubelet down or misconfigured, containerd down, broken static-pod manifests, etcd snapshot/restore, certificate inspection and renewal, static pods, kubeconfig/PKI |
| **B2** | `vm` | **Incus VM instances** on a Linux host with a copy-on-write storage pool. Golden images per Kubernetes version. Snapshot restore per trial | Full Linux VMs with their own kernel | kubeadm init/join/**upgrade** through distro packages, OS preparation (kernel modules, sysctl, swap, container-runtime install), HA control plane, CNI install, reboot/persistence, real node failure |

What the brief requires, and how this table meets it:
- **Two backend classes** (object-level vs system-level) are provided. The system-level class is split into a cheap tier (B1) and a high-fidelity tier (B2).
- **Both B1 and B2 exist** because the audit showed most CKA node-level competencies can be exercised faithfully in B1 at kind cost, while a small, important remainder genuinely needs a kernel: kubeadm upgrade, OS preparation, HA and reboot.
- **Every scenario declares its minimum class** (`backend.class`). Results record the class actually used.

---

## 1. Requirements derived from the audit

| # | Requirement | Evidence from the reference repositories |
|---|---|---|
| R1 | **Every** node, including the control plane, lives inside a resettable unit. | K16S runs the control plane on the host. One unsolved apiserver fault breaks the grader for every later task, and reset means rebuilding everything (k16s.md §7, §10). |
| R2 | Pinned versions, offline at trial time. | Unpinned Kubernetes versions: grindxhq has no `image:`; CK-X runs an unpinned k3s image; K16S has a floating Calico/Gateway fetch. Runtime `apt`, `dl.k8s.io/stable.txt` and GitHub downloads appear in grindxhq, CK-X and K16S. |
| R3 | Grader channel ≠ agent channel. The grader has privileged node access that the agent cannot tamper with. | K16S grades with `incus exec`, separated from the candidate's ssh (good). CK-X runs graders on the jumphost the candidate controls (bad). |
| R4 | Deterministic topology and naming, abstracted from scenarios. | K16S lightweight mode breaks tasks that hard-code `node01`/`controlplane`. grindxhq hard-codes kind container names in validators. |
| R5 | Fast, verifiable reset. | None of the audited repos has per-task reset plus verification. grindxhq's denylist sweep misses kube-system, CRDs, cordons and node files. |
| R6 | Kubernetes distribution matches the curriculum (kubeadm-built, upstream). | CK-X's "kind-cluster" is actually k3d/k3s, whose embedded components and paths differ from kubeadm clusters. |
| R7 | Linux host for experiments. Mac for authoring. CI on commodity runners for classes A and B1. | Project constraint. This host is Ubuntu 22.04, 16 vCPU, 31 GiB, cgroup v2, `/dev/kvm` present, Docker 29.6, LXD 5.0 snap installed but not initialised. |
| R8 | The agent must not reach anything outside the scenario environment. | This host holds several real-cluster kubeconfigs in `$HOME`. The agent workstation must mount **only** the generated kubeconfig and must have no route to other clusters or the internet. |

---

## 2. Backend A — `kind`

### 2.1 Why kind (vs. k3d, minikube, vcluster)

| Criterion | kind | k3d (k3s) | minikube | vcluster |
|---|---|---|---|---|
| Upstream kubeadm layout (static pods, `/etc/kubernetes/pki`, etcd) | ✅ | ❌ (embedded components, sqlite or embedded etcd) | ✅ (driver-dependent) | ❌ (virtual control plane) |
| Multi-node | ✅ | ✅ | limited | n/a |
| Used by upstream Kubernetes CI | ✅ | ❌ | ❌ | ❌ |
| Mac (Docker Desktop, Colima, OrbStack) | ✅ | ✅ | ✅ | ✅ |
| CI on GitHub-hosted runners | ✅ | ✅ | ✅ (heavier) | ✅ |
| Same image family can serve B1 (node exec) | ✅ | partial | partial | ❌ |
| License | Apache-2.0 | MIT | Apache-2.0 | Apache-2.0 |

**Recommendation: kind.** It is the only option that gives a kubeadm-shaped cluster *and* lets B1 reuse the same substrate. That makes A and B1 one code path with a capability flag, which halves backend implementation cost and keeps results comparable across classes.

### 2.2 Cluster profile (baked, versioned: `backends/kind/profiles/k8s-1.35-v1/`)

| Component | Choice | Rationale / note |
|---|---|---|
| Node image | `kindest/node:v1.35.x@sha256:…` | Matches curriculum v1.35. The digest is recorded in every result. |
| Topology | 1 control plane + 2 workers by default. Per-scenario override | Scheduling, affinity and taint scenarios need ≥2 workers. |
| CNI | kindnet, *if* it enforces NetworkPolicy in the pinned kind release. Otherwise Calico (Apache-2.0), pinned | **Verify in spike S-1.** NetworkPolicy scenarios need real enforcement, because the verifier uses positive and negative connectivity probes. K16S and CK-X graded NetworkPolicy structurally only. |
| Storage | local-path-provisioner (kind default), RWO | RWX scenarios are out of scope for A. |
| Metrics | metrics-server, pinned, `--kubelet-insecure-tls` | Needed for HPA and `kubectl top`. |
| Gateway / Ingress | Gateway API CRDs (standard channel, pinned) plus one controller. **Decision needed** (§7 D-3) | ingress-nginx was retired upstream (best-effort maintenance ended March 2026), so it should not be the default for a new benchmark. |
| LoadBalancer | cloud-provider-kind (Apache-2.0), pinned | Only needed for `CKA-NET-03` LoadBalancer scenarios. |
| Audit log | kube-apiserver audit policy via `kubeadmConfigPatches` + `extraMounts` | This is the authoritative **mutation trace**: every write is attributed to `kops-agent` vs `kops-verifier`. |
| Images | All add-on and scenario images preloaded (`kind load` or a baked image) plus a local pull-through registry | Offline trials (R2). The scenario lint rejects fixtures whose images are not in the manifest. |
| Identities | `kops-verifier` (cluster-admin, never given to the agent) and `kops-agent` (per `interfaces.agent_identity`) | Client-cert users, generated per cluster instance. |

### 2.3 Isolation and reset

| Option | Description | Isolation | Cost per trial *(est.)* | Recommendation |
|---|---|---|---|---|
| A. Fresh cluster per trial | `kind create` from the baked profile, then `kind delete` | Perfect | 30–60 s create, cached images | **Default** (`isolation: cluster`) |
| B. Namespace-scoped reuse | Shared warm cluster. The scenario owns declared namespaces. Reset = delete namespaces + baseline digest check | Good, if the scenario is truly namespaced and the digest check passes | ~5–15 s | Allowed only when `isolation: namespace` **and** the reset self-test proves baseline restoration |
| C. Snapshot/restore of node containers | `docker commit` / checkpoint | Unreliable for etcd and kubelet state | — | Rejected |

**Warm pool.** The runner keeps N pre-provisioned clusters, so provisioning time is off the critical path. The pool size is bounded by host RAM. A 3-node kind cluster with add-ons uses roughly 2–3 GiB *(est.)*, so this host can run 6–8 concurrent trials.

---

## 3. Backend B1 — `kind-node`

### 3.1 What a kind node actually is

A kind node is a privileged container running **systemd as PID 1**, **containerd**, **kubelet as a systemd unit**, `crictl`, and the kubeadm-generated `/etc/kubernetes/{manifests,pki,*.conf}`. The control plane runs as **static pods**, and etcd is stacked. So "stop kubelet", "break `/var/lib/kubelet/config.yaml`", "corrupt the kube-scheduler manifest", "etcd snapshot save/restore", "inspect or renew certificates" and "create a static pod" are all *real* operations against real components.

The K16S audit concluded that privileged LXC workers are "roughly as faithful as kind for workers" (k16s.md §10). B1 gets the same fidelity **and** keeps the control plane inside a disposable container (R1), which K16S lacks.

### 3.2 What KOPS adds (derived node image, built by KOPS)

- `openssh-server`, key-only root login, keys generated per cluster instance. The agent reaches nodes with `ssh <node>` from its workstation, which is the exam-realistic interface. grindxhq apt-installs sshd at runtime; KOPS bakes it into the image instead (R2).
- `etcdctl`/`etcdutl` pinned to the cluster's etcd minor version.
- Stable node aliases (`cp-1`, `worker-1`, `worker-2`) exposed through workstation `/etc/hosts` and ssh config. Scenarios refer to **roles**; the runner resolves them (R4).
- The grader reaches nodes through `docker exec` from the runner. The agent reaches nodes only through ssh from the workstation (R3).

### 3.3 Fidelity limits (explicit, and recorded in scenario metadata)

| Works in B1 | Does **not** work in B1 (needs B2) |
|---|---|
| systemd units: kubelet, containerd (`systemctl`, `journalctl`) | Kernel modules, non-namespaced sysctls (host-global) |
| Static-pod control plane faults and repair | Swap-related kubelet behaviour |
| etcd snapshot save / restore (manifest `--data-dir` change) | Reboot persistence (a container restart is not a boot) |
| PKI inspection; `kubeadm certs check-expiration` and `renew` | kubeadm **upgrade** through distro packages. Binaries could be staged, but that is not the real workflow |
| Static pods on workers | OS preparation for installing a cluster (`CKA-ARC-02`) |
| Node NotReady via kubelet or containerd failure | HA control plane with a real load balancer and multiple etcd members (possible in kind but awkward) |
| kubeadm `reset`/`join` of a worker *(experimental; spike S-1)* | Per-node resource capacity. Nodes see host capacity |

### 3.4 Safety

Node containers are privileged, so root inside a node is effectively root on the host's Docker engine. The KOPS threat model treats the agent as **non-adversarial but potentially destructive**. Mitigations:

1. Run experiments on a dedicated, disposable **runner VM**, not on a shared lab host.
2. Give the agent workstation no Docker socket and no host mounts.
3. Put the workstation on an isolated network that reaches only the cluster API and nodes.
4. Include a post-trial host health check in the runner.

---

## 4. Backend B2 — `vm`

### 4.1 Options evaluated

Scores run from 1 (poor) to 5 (excellent). *(est.)* marks unmeasured claims.

| Criterion | Incus **LXC** system containers (K16S model) | **Incus VMs** | libvirt + QEMU/KVM (cloud image + qcow2 overlays) | Lima | Cloud VMs |
|---|---|---|---|---|---|
| Linux fidelity (own kernel, modules, sysctl, swap, reboot) | 2 (shared kernel; same limits as B1) | **5** | **5** | 5 | 5 |
| Reproducibility (golden image, pinned) | 4 | **5** (images plus snapshots in one tool) | 5 | 4 | 3 (provider drift) |
| Reset speed | 4 (CoW snapshot restore) | **4** (CoW restore + boot, ~20–60 s *(est.)*; stateful snapshot possibly faster, spike S-2) | 4 (overlay discard or internal snapshot with RAM) | 2 (snapshots qemu-only/experimental) | 1 |
| Mac development | 3 (inside a Lima VM) | 2 (nested virt needed inside a Mac VM; Apple M3+/macOS 15 only) | 2 | **5** | 4 |
| CI feasibility | 3 | 3 (needs `/dev/kvm`; GitHub-hosted Linux runners expose KVM; self-hosted lab runner for full runs) | 3 | 2 | 2 (cost, credentials) |
| Resource cost per 3-node cluster | **low** | medium (~6–8 GiB *(est.)*) | medium | medium | $$ |
| Implementation complexity | medium (the K16S knob list shows it is fiddly) | **low–medium** (one CLI/API for images, networks, snapshots, projects) | medium–high (networking, image pipeline, snapshots all DIY) | medium (multi-VM networking is awkward) | high |
| Security isolation from host | ❌ privileged | ✅ | ✅ | ✅ | ✅ |
| Adds competencies beyond B1? | Only apt-based package flows | **Yes**: upgrade, OS prep, HA, reboot | Yes | Yes | Yes |
| License | Apache-2.0 (Incus) | Apache-2.0 | LGPL/GPL tools, used as external programs | Apache-2.0 | n/a |

### 4.2 Recommendation

**B2 = Incus VM instances**, on a Linux experiment host with a btrfs or ZFS storage pool.

- **Why not LXC for B2?** It adds almost nothing over B1: same shared-kernel limits, weaker isolation, more setup. K16S itself had to put every hard system task on the host because of this.
- **Why Incus over raw libvirt?**
  - Same fidelity.
  - A single tool covers image management, CoW snapshots and restore, isolated networks, projects (one per trial pool) and a REST API.
  - Less bespoke code for KOPS to maintain.
  - libvirt remains the fallback if Incus is unavailable on the experiment host.
- **Why not Lima as the B2 engine?** It is good for developer ergonomics on a Mac, but weak for multi-VM clusters and snapshot pools. Proposed Mac story: author and test A/B1 scenarios locally with Docker; run B2 on the shared Linux runner, or inside a Lima VM on nested-virt-capable Macs.
- **Host note.** This host has the LXD 5.0 snap installed (uninitialised). Incus and LXD should not both manage bridges on one host. Choose one (§7 D-2). Incus is recommended because it is Apache-2.0 and community-governed; LXD's newer releases are AGPL with a CLA.

### 4.3 Golden images and reset

- **Image build.** An image recipe authored by KOPS (cloud-init + shell) produces `kops-node-k8s-1.35` with pinned containerd, kubeadm, kubelet and kubectl, and all images pre-pulled.
- **Cluster images.**
  - "Clean cluster" snapshot: kubeadm init + join + CNI done.
  - "Bare nodes" snapshot: packages only. This is for kubeadm install and join scenarios.
- **Per-trial reset.** Restore the snapshot for all instances, boot, then run a health gate (nodes Ready, baseline digest).
- **Clock handling.** After restore, force a time sync before setup. This avoids certificate and lease anomalies, especially with stateful snapshots.

---

## 5. Backend interface (implemented once per class)

```python
class Backend(Protocol):
    name: str                                    # "kind" | "kind-node" | "vm"
    capabilities: BackendCapabilities            # features, node_access, fidelity flags

    def provision(self, spec: BackendSpec) -> EnvHandle: ...        # from scenario.backend (+ pool)
    def health(self, env: EnvHandle) -> HealthReport: ...
    def kubeconfig(self, env: EnvHandle, identity: Literal["verifier", "agent"]) -> Path: ...
    def node_exec(self, env: EnvHandle, node_role: str, argv: list[str],
                  stdin: bytes | None = None, timeout_s: int = 60) -> ExecResult: ...  # setup/verifier ONLY
    def workstation(self, env: EnvHandle, tools: set[str]) -> WorkstationHandle: ...   # agent sandbox
    def baseline_digest(self, env: EnvHandle, scope: DigestScope) -> str: ...
    def reset(self, env: EnvHandle, strategy: ResetStrategy) -> None: ...
    def destroy(self, env: EnvHandle) -> None: ...
    def fingerprint(self, env: EnvHandle) -> EnvFingerprint: ...    # versions + image digests → results
```

**The agent workstation** is a separate container on the environment's isolated network. It holds:
- the pinned CLI tools allowed by `interfaces.allowed`;
- the agent kubeconfig;
- ssh keys for nodes when `node_access: ssh`;
- a scratch home directory.

It does **not** hold `scenario.yaml`, `verify/` or `reference/`, verifier credentials, the Docker socket, internet access, or any host kubeconfig. The same workstation image is used for every agent; its digest is recorded.

---

## 6. Capability-aware scoring (idea adapted from K16S `requires: heavy`)

A scenario is run only on backends with `class ≥ scenario.backend.class` (ordering: kind < kind-node < vm) and a superset of `features`.

Profile reports state the **denominator per backend class**, e.g. "CKA Troubleshooting: 7 scenarios, of which 3 require kind-node and 1 requires vm". This means:
- a missing backend shows up as *uncovered competency*, not silently dropped;
- a system-level scenario is never run in a degraded form and counted.

---

## 7. Decisions requested

> **Review status (2026-09-28, see [decision-log.md](decision-log.md)):** D-1 approved (B1 for the slice). D-2 **deferred**: B2 is not built now, spike S-2 is not scheduled, and `vm` families are reported as "uncovered: backend deferred". D-3 approved (single dual-mode controller, chosen in S-1). D-4 approved (decided by S-1 measurement). D-5 approved (pin 1.35).

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| D-1 | Is B1 (`kind-node`) acceptable as "system-level" for the vertical slice? | (a) yes, B2 later; (b) build B2 before any system scenario | **(a)**. B1 covers the most common CKA node and component troubleshooting at kind cost. B2 is only needed for upgrade, OS prep, HA and reboot. |
| D-2 | B2 engine | Incus VMs / libvirt / LXD (already installed) | **Incus VMs**, subject to spike S-2. Keep libvirt as the fallback. |
| D-3 | Gateway/Ingress controller for A | Envoy Gateway (Gateway only) + separate Ingress controller / a single controller supporting both Ingress and Gateway API (e.g. Traefik) / NGINX Gateway Fabric + separate Ingress controller | A single dual-mode controller. It minimizes add-ons and keeps Ingress and Gateway scenarios on one data plane. Pin and review the license before adoption. |
| D-4 | CNI for A/B1 | kindnet (if NetworkPolicy enforcement is verified) / Calico | Measure in spike S-1. Prefer kindnet, which has fewer moving parts. Calico is the fallback. |
| D-5 | Kubernetes version policy | Pin 1.35 (curriculum) / track latest | **Pin 1.35** for benchmark v1. Revisit when CNCF publishes the next curriculum. |

## 8. Spikes before freezing (no scenario work depends on their outcome except D-4)

- **S-1 (kind/kind-node, ~2 days):**
  - Measure create/delete time and RAM for the profile.
  - Verify NetworkPolicy enforcement.
  - Verify the audit log captures agent vs verifier identities.
  - Verify that stop kubelet, break the scheduler manifest, and etcd snapshot/restore behave, and that the cluster is fully recoverable by recreation.
  - Try kubeadm reset/join of a worker.
- **S-2 (Incus VMs, ~3 days):**
  - Build a golden image.
  - Measure snapshot restore + boot + health gate time.
  - Test stateful snapshots.
  - Run a 3-node kubeadm cluster restore under load.
