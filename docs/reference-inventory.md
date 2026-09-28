# Reference Repository Inventory (A)

- **Audit date:** 2026-09-26.
- **Method:** static code reading plus git history inspection. Nothing under `references/` was executed or modified; `git status` is clean for all 8 repositories after the audit.
- **Machine-readable version:** [`reference-inventory.csv`](reference-inventory.csv), one row per repository with all 32 audit fields.
- **Per-repository architecture notes:** [`references/`](references/).

## 1. Corrections to the brief's assumptions

These are the facts the audit changed. Each is verified in the repositories (evidence in the per-repo notes).

| # | Brief assumed | Audit found | Consequence for KOPS |
|---|---|---|---|
| 1 | ckad-2026 has 55 tasks | **78** question folders (Q01–Q78) | Counts in all KOPS docs use 78. |
| 2 | CK-X is kind-based | The "kind-cluster" container is privileged DinD running **k3d v5.8.3 (k3s)**. `KIND_DEFAULT_VERSION` is set but unused. | CK-X gives no evidence about kubeadm/kind fidelity. Its lack of node access explains zero etcd, kubelet or cert tasks. |
| 3 | CK-X license is BSL 1.1 | BSL 1.1 at HEAD, but **MIT from the initial commit until `b837387` (2026-05-09)**. The last MIT revision is `199f4be`. | We still treat it as reference-only (quality and contamination). The MIT history is recorded in case a future reuse decision needs it. |
| 4 | ckad-exams is MIT | README shows an MIT badge, but **there is no LICENSE file in the tree or anywhere in git history**. The default is all rights reserved. | **No reuse of any kind.** Cite only. |
| 5 | ckad-dojo: CC BY-NC-SA, reference only | **Verbatim killer.sh "CKAD Simulator Kubernetes 1.34" (3,293 lines, 28 "killer" markers) sits in git history** from the initial commit `ce200ed`/`5646e61` until `2b839f8` (2025-12-09). killer.sh-derived scoring functions, manifests and templates are still at HEAD, and `scripts/ckad-score.sh:113` still sources them as a fallback. Some simulations are recall-sourced. | **Quarantined** as a content source. Its architecture is studied from code only. Its fingerprints feed the KOPS contamination denylist. |
| 6 | ckad-2026: GPL, problem-family knowledge usable | Q01–Q16 share titles, order and entity names with ckad-dojo sim4, which is adapted from a recall-style third-party list. | Q01–Q16 are **quarantined**. Q17–Q78 are usable at the *topic* level only, which adds nothing beyond the public curriculum. |
| 7 | cka-hand-on-lab has "55+" tasks | **47** YAML tasks. The v2 content carries Claude co-author trailers. Node-level faults are described but never injected. | Ideas only. |
| 8 | K16S is a full system-level lab | Only workers are LXC containers. **The control plane is the host itself**, so control-plane faults hit the grader's host, and reset means a full rebuild. | Drives backend requirement R1: every node must live in a resettable unit (backend-design.md). |

## 2. Summary table

| Repo | Tier | License | Lang | Certs | Tasks | Env / provisioning | Verification | Reset | Node access | Tests | Contamination | KOPS use |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| grindxhq-cka | P0 | Apache-2.0 | Go/Wails/React | CKA | 86 (359 checks) | kind (unpinned) + bastion, multi-cluster | shell cmd + string match, host-side, 5 s, no polling | denylist sweep | ssh → kind nodes (etcd, static pods, certs) | **E2E self-test runner** (not in CI) | low–med | ideas; code reuse possible with attribution |
| k16s | P0 | PolyForm NC 1.0.0 | Bash/Go/Svelte | CKA, CKS | 87 | kubeadm 1.33: host control plane + privileged Incus LXC workers; Lima; kind-lite | `validate.sh` exit code, root on host, 30 s | none per task; rebuild | real systemd/kubelet in LXC workers | 1 lint test | low–med | architecture only |
| ck-x | P0 | BSL 1.1 (MIT < 2026-05-09) | Bash/Node | CKA, CKAD, CKS, Docker, Helm | 111 (329 steps) | compose + DinD **k3d** | exit-code step scripts via ssh to jumphost, weighted, no timeouts | cluster delete per exam | none (jumphost root only) | none | medium | architecture only |
| ckad-2026 | P0 | GPL-3.0 | Bash/MD | CKAD | **78** | current kubeconfig, namespace per task | jsonpath checks, exit always 0 | none | minimal | none | **med (Q01–16 high)** | topic-level only; Q01–16 quarantined |
| ckad-dojo | P0 | CC BY-NC-SA 4.0 | Bash/Python/JS | CKAD | 398 (~65–75 types) | existing cluster + host docker + registry + helm | bash `score_qN` + keyword-heuristic details | destructive pattern cleanup | host shell | CI lint/structural; no cluster E2E | **HIGH** | **quarantined**; architecture only |
| cka-hand-on-lab | P1 | MIT | Rust/Bash | CKA | 47 | minikube single node | `sh -c` + substring (4 always-pass) | recreate minikube | described, not provided | none | low–med | ideas only |
| ckad-exams | P1 | **none** | Bash/YAML | CKAD | 30 | single cluster | bash, incl. behavioral probes | delete ns on pass | minimal | none | low–med | **no reuse** |
| ckad-exercises | P1 | MIT | Markdown | CKAD | 152 | any | none | none | none | none | **high (memorized)** | coverage checklist + canary list |

## 3. Per-repository audit fields

All 20 requested fields are in the CSV. The key points per repository follow.

### 3.1 grindxhq-cka (`ea74cdb`)

- **Purpose:** Wails desktop CKA simulator.
- **Content:** 86 tasks across 5 sessions, 13 of them node-level.
- **Environment:** 1–4 kind clusters per session plus one bastion container, with ssh into kind nodes.
- **Task schema:** one YAML per task. Setup and validation are hidden from the UI through `json:"-"`. The solution is returned by the API.
- **Verification:** runs on the **host** as `sh -c` with a 5 s timeout and 4 string matchers.
- **Scoring:** per-question all-or-nothing, weighted.
- **Main strength:** `cmd/test-runner` is an **E2E setup → solution → validate** self-test.
- **Main weaknesses:**
  - no negative control, so s5-11 and s2-15 validators pass on the initial state;
  - files and kubeconfig graded on the host while the user works in the bastion;
  - a context race during setup;
  - unpinned versions;
  - incomplete reset.

### 3.2 k16s (`08f0ba1`)

- **Environment:** real kubeadm (1.33), Calico and metrics-server. The **control plane runs on the host**. Workers are privileged Incus LXC containers configured with nesting, kmsg, host-loaded modules and unconfined AppArmor. There is also a Lima laptop mode and a kind "lightweight" mode.
- **Task format:** YAML plus `setup.sh`/`validate.sh`, with a capability tag (`requires: heavy`) that removes unsupported tasks from the score denominator.
- **Reset:** none per task. Only 2 of 87 tasks touch the worker system layer.
- **Verification bug:** several validators poll longer than the 30 s check timeout.
- **Most valuable output for KOPS:** the LXC fidelity analysis, used as a checklist.

### 3.3 ck-x (`76a7894`)

- **Architecture:** a facilitator state machine (Redis). All actions go over ssh to a jumphost, which drives a **k3d** cluster inside DinD.
- **Content:** 7 labs with 111 questions and 329 weighted steps. Graders follow an exit-code contract.
- **Weaknesses:**
  - graders are visible to the user;
  - setup failures are swallowed;
  - 5 validators are missing and 71 are orphaned;
  - there are no timeouts;
  - telemetry is on by default.
- **Node access:** none, so there are zero etcd, kubelet or cert tasks.

### 3.4 ckad-2026 (`9d66dd8`)

- **Content:** 78 × {QUESTION, setup, check, ANSWER}, one namespace per task.
- **Verification:** static jsonpath checks with no behavioral checks. The exit code is always 0.
- **Reset:** none.
- **Provenance:** Q01–Q16 share a recall-list lineage with ckad-dojo sim4.

### 3.5 ckad-dojo (`b668622`)

- **Content:** 20 simulations, 398 questions.
- **Architecture:** Python CLI and web server over bash libraries. Each exam has an `exam.conf` manifest listing the namespaces and Helm releases it owns, plus a `post-setup.sh` fault hook.
- **Verification:** weighted `score_qN` functions. Criterion pass/fail is parsed from keyword heuristics and matched to questions **by position**.
- **Cleanup:** destructive and pattern-based.
- **Provenance:** see correction 5 above.

### 3.6 P1

- **cka-hand-on-lab:**
  - schema-first YAML, but the schema is never enforced;
  - weak verifiers (4 always pass);
  - setup is not wired into the tool;
  - exam mode is self-graded.
- **ckad-exams:**
  - bash validators that include good behavioral probes (positive and negative NetworkPolicy probes, `helm get values`);
  - but it grades re-applied files rather than live state, and one validator applies the reference answer;
  - unlicensed.
- **ckad-exercises:** 152 non-executable drills, heavily memorized by models.

## 4. What the whole corpus lacks (design gaps KOPS must fill)

| Capability | Present anywhere? |
|---|---|
| Negative control (verifier must FAIL before the solution) | **No** |
| Reference solution run through the *candidate's* access path | **No**. grindxhq runs it on the host. |
| Self-test in CI | **No**. grindxhq's runner exists but is not in CI. |
| Verified reset back to baseline | **No** |
| Behavioral NetworkPolicy/Service checks | Partially (ckad-exams, a few CK-X scripts) |
| Grader isolated from the candidate | Partially (K16S `incus exec`, grindxhq's host side) |
| Machine-readable, tri-state criterion results | **No**. dojo uses heuristic text; CK-X ignores stdout. |
| Versions pinned and offline | **No**. K16S pins Kubernetes but fetches CRDs and Helm online. |
| Control plane inside a resettable unit together with node access | **No**. grindxhq has kind nodes but no systemd faults; K16S has its host control plane. |
| Provenance record per task | **No** |
| Agent (non-human) interface or trace capture | **No**. All eight are human-oriented simulators. |
