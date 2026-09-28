# Initial Vertical Slice — Proposal (I)

**Status: PROPOSED. Nothing here is implemented.** This document specifies scenarios to be authored clean-room *after* architecture review.

The purpose of the slice is **to validate the pipeline**, not to measure models:

```
schema → lint → provision → setup → confirm → agent access → trace → verify → reset → self-test
```

Therefore:
- The 10 core scenarios are chosen for *pipeline diversity*: isolation modes, backend classes, check types, and fault layers.
- The certification mix follows the brief. **CKAD:** configuration, deployment, networking, observability. **CKA:** workloads/scheduling, networking, troubleshooting, and system/node-level problems.

All names below are placeholders. Real names come from seeded `task.parameters`, and none of the scenarios derives from any reference task text.

---

## 1. Overview

| # | Scenario id (proposed) | Family | CKA mapping | CKAD mapping | Backend / isolation | Difficulty | Key pipeline aspect validated |
|---|---|---|---|---|---|---|---|
| S01 | `kops-cfg-externalize-config-001` | PF-CFG-001 | WLS / CKA-WLS-02 | AEC / CKAD-AEC-05 | kind / namespace | 1 | Baseline happy path. HTTP probe of an app-reported value. Guard on image. |
| S02 | `kops-wkl-rollback-to-healthy-001` | PF-WKL-003 | WLS / CKA-WLS-01 | ADP / CKAD-ADP-02 | kind / namespace | 2 | Multi-revision setup. `k8s.rollout_complete`. Guard against delete/recreate (UID). |
| S03 | `kops-net-service-endpoint-repair-001` | PF-NET-003 | TRB / CKA-TRB-05 | SNW / CKAD-SNW-02 | kind / namespace | 2 | Two simultaneous faults. `k8s.endpoints` + `net.http`. Negative solution fixes only one fault. **Already drafted and schema-validated** ([example](examples/kops-net-service-endpoint-repair-001/)). |
| S04 | `ckad-obs-probes-slow-start-001` | PF-OBS-001 | — (disabled) | AOM / CKAD-AOM-02 | kind / namespace | 2 | `stability` window check. Single-profile scenario. Flakiness measurement (self-test ×3). |
| S05 | `cka-sch-dedicated-pool-001` | PF-SCH-002 | WLS / CKA-WLS-05 | — (disabled) | kind (3 nodes) / **cluster** | 2 | Multi-node topology with node-role resolution. Guards on node taints and labels (cluster-scoped). Cluster-isolation reset. |
| S06 | `kops-net-policy-isolation-001` | PF-NET-004 | NET / CKA-NET-02 | SNW / CKAD-SNW-01 | kind + `networkpolicy` / namespace | 2 | Connectivity **matrix** with positive and negative probes. Positive-control → `error` semantics. CNI enforcement (spike D-4). |
| S07 | `kops-sto-bind-existing-volume-001` | PF-STO-002 | STO / CKA-STO-03 | ADB / CKAD-ADB-04 | kind / **cluster** (PV is cluster-scoped) | 2 | Stateful data-marker check via verifier exec. Guard that the PV is not recreated (data preserved). |
| S08 | `kops-sec-forbidden-least-privilege-001` | PF-SEC-003 | ARC / CKA-ARC-01 | AEC / CKAD-AEC-02 | kind + `audit-log` / namespace | 2 | `k8s.can_i` allow **and deny** matrix. Diagnosis from workload logs. Audit-log mutation trace. Anti-shortcut guard (no broad roles). |
| S09 | `cka-nod-kubelet-notready-001` | PF-NOD-001 | TRB / CKA-TRB-01 | — | **kind-node** / cluster | 3 | Node ssh from workstation. `node.systemd` (active **and** enabled). `node.exec`. Settle up to 120 s. Grader channel (docker exec) separate from agent channel (ssh). |
| S10 | `cka-nod-scheduler-manifest-001` | PF-NOD-003 | TRB / CKA-TRB-02 | — | **kind-node** / cluster | 3 | Control-plane static-pod fault fully contained in a disposable node (R1). Behavioural recovery (probe pod gets scheduled). Guard: other manifests unchanged. |
| S11* | `cka-net-coredns-repair-001` | PF-NET-009 | NET / CKA-NET-06 | — | kind / cluster | 2 | *Stretch.* kube-system mutation plus cluster reset. `net.dns`. |
| S12* | `cka-clu-etcd-snapshot-001` | PF-CLU-001 | ARC / CKA-ARC-04 | — | kind-node / cluster | 2 | *Stretch.* `artifact` check with a verifier-side validator (`etcdutl snapshot status` + marker key restored in a scratch dir). |

**Profile coverage of the core slice (S01–S10):**

| Profile | Scenarios | Domains covered |
|---|---|---|
| CKA | 9: S01, S02, S03, S05, S06, S07, S08, S09, S10 | All 5. STO: S07. TRB: S03, S09, S10. WLS: S01, S02, S05. ARC: S08. NET: S06. |
| CKAD | 7: S01, S02, S03, S04, S06, S07, S08 | All 5. ADB: S07. ADP: S02. AOM: S04. AEC: S01, S08. SNW: S03, S06. |

- **Dual-profile scenarios:** 6 (S01, S02, S03, S06, S07, S08).
- **Single-profile:** S04 (CKAD only); S05, S09, S10 (CKA only).

This exercises the rule that each profile maps to exactly one primary competency.

**Backend coverage:** 8 × `kind` and 2 × `kind-node` (plus 1 more in stretch). `vm` is intentionally absent from the slice (decision D-1 in backend-design.md).

---

## 2. Scenario specifications

Each "agent-visible gist" is a summary for reviewers. The real `task.md` is written during implementation.

### S01 — Externalize application configuration (PF-CFG-001)

- **Initial state.** A Deployment runs a small KOPS-authored HTTP app. The app reports its effective configuration at `/config`, and its settings are currently baked into env literals. A config file is provided in the workstation.
- **Agent-visible gist.** Move the application's settings into a ConfigMap. Expose one key as an environment variable and mount the file at a given path. The running app must report the new values.
- **Invariants.**
  - Goal: ConfigMap has the required keys.
  - Goal: `/config` over `net.http` reports the expected values.
  - Goal: the env var uses `configMapKeyRef`.
  - Goal: rollout complete.
  - Guard: container image unchanged.
- **Negative solution.** Set the env literal to the new value without a ConfigMap. Must FAIL on the `configMapKeyRef` criterion.

### S02 — Roll back to the last healthy revision (PF-WKL-003)

- **Initial state.** A Deployment has 4 revisions. The seed decides which earlier revision is healthy. The latest revision's pods never become Ready: the image is valid, but an env flag makes the readiness endpoint fail. So the rollout is stuck and progress is exceeded.
- **Gist.** Restore the service to the most recent revision that worked. Do not delete the Deployment.
- **Invariants.**
  - Goal: `k8s.rollout_complete`.
  - Goal: the pod template env and image equal the healthy revision's.
  - Goal: N ready replicas.
  - Guard: Deployment UID unchanged.
  - Guard: Service unchanged.
- **Negative solutions.**
  - `rollout undo` to the immediately previous revision, when that revision is also broken. Must FAIL.
  - Delete and re-create the Deployment. Must FAIL the UID guard.

### S03 — Restore traffic to a Service with no endpoints (PF-NET-003)

This is the drafted example. Two faults: a wrong selector and a wrong targetPort.

- **Guards.** Pod template unchanged. Service UID and ClusterIP unchanged.
- **Negative solutions.** Fix the selector only. Recreate the Service.

### S04 — Make a slow-starting app stable (PF-OBS-001)

- **Initial state.** The app has a seeded startup delay of 30–60 s. An aggressive liveness probe kills it before it starts, causing CrashLoopBackOff. There is no readiness probe.
- **Gist.** Configure health checks so the app starts reliably and only receives traffic when ready. Do not change the app's startup behaviour or image.
- **Invariants.**
  - Goal: rollout complete.
  - Goal: `stability` of `restartCount` unchanged over a 60 s window, with 6 samples.
  - Goal: a readiness probe targets the readiness endpoint.
  - Goal: EndpointSlice excludes pods during their startup phase. This is checked via a controlled restart in the verifier; decide during implementation if it is too complex.
  - Guard: the env var controlling startup delay is unchanged.
  - Guard: image unchanged.
- **Negative solution.** Remove the liveness probe entirely. The stability check passes, but readiness semantics FAIL.

### S05 — Run a workload on a dedicated node pool (PF-SCH-002)

- **Initial state.** A 3-node cluster. The worker resolved as `pool-analytics` carries a protective taint and a label. A Deployment is Pending because it has a nodeSelector but no toleration.
- **Gist.** Make the workload run only on the dedicated pool. Leave the node protections in place.
- **Invariants.**
  - Goal: all pods Running on the pool node.
  - Goal: tolerations present.
  - Guard: node taints unchanged.
  - Guard: node labels unchanged on all nodes.
- **Negative solution.** Remove the taint. Must FAIL the guard.

### S06 — Isolate a backend with NetworkPolicy (PF-NET-004)

- **Initial state.**
  - Namespaces: `app` (backend API plus a same-namespace "batch" pod), `web` (a client labelled with the frontend role, and an unlabelled client), and `other` (a client).
  - No policies exist.
- **Gist.** Only frontend-role pods from the web namespace may reach the backend on its API port. All other ingress to the backend is denied, including from its own namespace. DNS for all workloads must keep working.
- **Invariants.**
  - Goal: `net.http` reachable from web/frontend.
  - Goal: blocked from web/unlabelled, from other, and from app/batch.
  - Goal: `net.dns` still resolves from the backend namespace.
  - Guard: no policies modified in other namespaces.
- **Positive control.** Each probe source must first reach a control target. If it can't, the criterion is `error`, and the trial is INVALID.
- **Negative solution.** A policy that selects the namespace only, without the pod label. Must FAIL (the unlabelled client gets through).

### S07 — Bind a workload to its existing data volume (PF-STO-002)

- **Initial state.** A pre-provisioned PV (Retain policy) holds a seeded data marker. The app's PVC is Pending because it requests a non-existent StorageClass, and a default dynamic class exists that would create an *empty* volume.
- **Gist.** Get the application running using its existing data. The data must not be lost.
- **Invariants.**
  - Goal: the PVC is Bound to *that* PV (volumeName).
  - Goal: the pod is Ready.
  - Goal: the verifier reads the marker file with `kubectl exec` and gets the seeded value.
  - Guard: PV UID unchanged.
  - Guard: PV reclaimPolicy is still Retain.
- **Negative solution.** Switch the PVC to the default class. It binds to a new empty volume, so the marker check FAILS.

### S08 — Fix a Forbidden error with least privilege (PF-SEC-003)

- **Initial state.** A reporting workload (KOPS-authored) uses its own ServiceAccount and logs 403 errors. It needs to list and watch pods, and get one named ConfigMap, in its namespace.
- **Gist.** The workload is failing. Find out why and fix it without granting more access than it needs.
- **Invariants.**
  - Goal: `k8s.can_i` allows exactly the required verbs.
  - Goal: the workload reports success (its status endpoint or logs show the marker).
  - Guard: `k8s.can_i` **denies** delete pods, get secrets, the same verbs in another namespace, and cluster-wide list.
  - Guard: the SA is not bound to any built-in broad role (admin, edit, cluster-admin).
- **Negative solution.** Bind the `edit` ClusterRole. The goal passes, but the guards FAIL.

### S09 — Recover a NotReady node (PF-NOD-001, kind-node)

- **Initial state.** On the node resolved as `worker-1`, a kubelet systemd drop-in points to a non-existent config path, so kubelet crash-loops and the node goes NotReady. The seed picks one of three root causes:
  1. a wrong config path in the drop-in;
  2. an invalid config field;
  3. the unit is stopped *and* disabled.
- **Gist.** A node has stopped accepting workloads. Restore it so it survives a kubelet restart.
- **Invariants.**
  - Goal: node Ready=True, with settle up to 120 s.
  - Goal: `node.systemd` kubelet active **and** enabled.
  - Goal: a verifier probe pod pinned to the node becomes Ready.
  - Goal: `node.exec` confirms that `systemctl cat kubelet` references existing files.
  - Guard: node object UID unchanged (the node was not deleted and re-registered).
  - Guard: the canonical kubelet config file is unchanged, except in the root-cause variant where it *is* the fault.
- **Negative solution.** `systemctl start kubelet` without fixing the drop-in or enabling the unit. This FAILS on persistence or on Ready, depending on the variant.

### S10 — Restore scheduling after a control-plane fault (PF-NOD-003, kind-node)

- **Initial state.** The kube-scheduler static-pod manifest is modified. The seed picks one of: a wrong kubeconfig path, a wrong image tag, or an invalid flag. The scheduler pod fails, and newly created pods stay Pending.
- **Gist.** New workloads are not being placed on nodes. Restore normal operation.
- **Invariants.**
  - Goal: the scheduler mirror pod is Ready.
  - Goal (behavioural): a verifier probe pod gets `PodScheduled=True` within 30 s.
  - Goal: the manifest's fault field is restored to a valid value.
  - Guard: the other control-plane manifests are unchanged (hash).
  - Guard: the scheduler manifest differs from the original only in fields listed in an allowlist (semantic diff).
- **Negative solution.** Run a replacement scheduler as a Deployment. That breaks the "static pod restored" goal.

---

## 3. Pipeline coverage checklist

| Pipeline element | Covered by |
|---|---|
| Namespace isolation + reset digest | S01, S02, S03, S04, S06, S08 |
| Cluster isolation (destroy/recreate) | S05, S07, S09, S10 (S11) |
| Multi-node topology and role resolution | S05, S09 |
| Backend features: networkpolicy, audit-log, default-storageclass | S06, S08, S07 |
| Check types: `k8s.field/condition/rollout_complete/endpoints/unchanged/can_i` | S01–S08 |
| Check types: `net.http`, `net.dns` | S01, S03, S06 (S11) |
| Check types: `stability` | S04 |
| Check types: `node.systemd`, `node.exec`, `node.file` | S09, S10 |
| Check types: `artifact` | (S12) |
| Seeded root-cause variants | S02, S09, S10 |
| Negative solutions (verifier mutation tests) | all |
| Agent tools: kubectl/shell/file I/O | all |
| Agent tools: ssh to nodes | S09, S10 |
| Audit-log mutation trace | all (S08 asserts on it in self-test) |
| INVALID semantics (positive-control failure) | S06 |

---

## 4. Implementation plan (after approval) and acceptance criteria

| Milestone | Content | Acceptance |
|---|---|---|
| M0 | Spike S-1 (backend-design.md §8). Decisions D-1…D-5. | Measurements recorded. CNI and controller chosen. |
| M1 | Registry + lint + schemas + contamination scan | Example S03 lints clean. The negative schema tests pass. Denylist hits are detected on synthetic inputs. |
| M2 | `kind` backend (profile, warm pool, digest, identities, audit log) + workstation image | Provision → health → digest → destroy is reproducible, with fingerprints recorded. |
| M3 | Setup/confirm + verifier engine (k8s.*, net.*, stability) + result recorder | S01–S03 self-test green ×3 on fresh instances. Negative solutions FAIL. |
| M4 | Tool Gateway + trace recorder + Reference Scaffold + one OpenAI-compatible adapter + a null agent + a scripted "oracle agent" | The oracle agent (it replays reference/solution.sh through the gateway) PASSes. The null agent FAILs. Traces are complete. |
| M5 | S04–S08 | All green in self-test. Reset digests match. |
| M6 | `kind-node` capability (derived image, ssh, node exec) + S09, S10 | Self-test green ×3. The host post-trial health check is clean. |
| M7 | Pilot: 1 local SLM + 1 frontier model × 10 scenarios × 3 seeds × 3 trials | This is a pipeline shake-down, not a result. Check that INVALID < 2% and that no verifier flakes occur on oracle runs. |

A scenario reaches `validated` only through `kops selftest` (runtime-architecture.md §6). Nothing enters an experiment otherwise.
