# Reuse Register (J)

This file is the **single gate** for anything from outside KOPS that enters the KOPS repository. An artefact not listed here must not be copied. Every entry records: source repository, source path, license, reason for reuse, modification, and attribution requirement (as required by the brief §5).

**Status as of 2026-09-26: zero code fragments reused.** One content item is reused: the CNCF curriculum text, CC-BY 4.0.

---

## J.1 Ideas reused (reimplemented independently; no code or text copied)

Ideas and architecture are not copyrightable. They are still listed here for scholarly attribution and to make the design lineage auditable.

| # | Idea | Source(s) | License of source | Where it lands in KOPS |
|---|---|---|---|---|
| I-1 | **Benchmark self-test**: setup → reference solution → same validators must pass | grindxhq-cka `cmd/test-runner` | Apache-2.0 | `kops selftest`, extended with negative control, null agent, negative solutions, gateway path, ×3 determinism and reset digest (runtime-architecture.md §6) |
| I-2 | Declarative per-check validation list with hidden validators | grindxhq-cka `internal/question`, `internal/validator` | Apache-2.0 | `criteria.yaml` typed checks (criteria.schema.json) |
| I-3 | Bastion/workstation on the cluster network with ssh to nodes; kubeconfig server rewrite for in-network clients | grindxhq-cka `internal/cluster/bastion.go` | Apache-2.0 | Agent workstation and B1 node access (backend-design.md §3, §5) |
| I-4 | Cluster health → reuse / reset / recreate lifecycle; parallel create | grindxhq-cka `internal/cluster/kind.go` | Apache-2.0 | Backend provisioner warm pool |
| I-5 | Capability tag excluding unsupported tasks from the score denominator | k16s `requires: heavy` | PolyForm NC | `backend.class` + `features`; per-class denominators (backend-design.md §6) |
| I-6 | Lint test tying capability tags to backend-specific commands | k16s `server/questions_test.go` | PolyForm NC | Lint rule: no `node.*` criteria on `kind` scenarios |
| I-7 | Grader channel separate from the candidate channel | k16s (`incus exec` vs candidate ssh) | PolyForm NC | Verifier identity + runner-side node exec (backend-design.md R3) |
| I-8 | Checklist of what kubelet needs inside a system container | k16s `provision/incus.sh` analysis | PolyForm NC | Requirements for the B1 derived node image and the B2 design (checklist only) |
| I-9 | Step-level graders with a simple exit-code contract | ck-x `facilitator/assets/exams/**/validation` | BSL 1.1 | Tri-state `script` criterion contract |
| I-10 | Explicit trial state machine; re-evaluation because graders are read-only | ck-x `facilitator/src/services` | BSL 1.1 | Trial states (runtime-architecture.md §1) |
| I-11 | One namespace per task | ckad-2026, ckad-exams, ckad-dojo | GPL-3.0 / none / CC BY-NC-SA | `backend.isolation: namespace` + `backend.namespaces` |
| I-12 | Manifest listing the resources a task owns → ownership-based cleanup | ckad-dojo `exam.conf` | CC BY-NC-SA | Owner labels + namespace declaration + baseline digest |
| I-13 | Split between declarative seeds and an imperative fault hook | ckad-dojo `post-setup.sh` | CC BY-NC-SA | `fixtures/` + `setup/setup.sh` + typed `initial_state.faults` |
| I-14 | Positive + negative connectivity probes for NetworkPolicy | ckad-exams validators | none (unlicensed; described in our own words only) | `net.http`/`net.tcp` with `expect: reachable/blocked` + positive control |
| I-15 | Verify through the intended mechanism (e.g. Helm release values, not only objects) | ckad-exams | none (idea only) | PF-PKG-001 invariants |
| I-16 | Schema-first task manifests with domain-prefixed ids | cka-hand-on-lab `tasks/schema.json` | MIT | scenario.schema.json (strict, enforced in CI) |
| I-17 | Curriculum domain tags plus a coverage matrix | ckad-dojo `docs/simulation-coverage.csv` | CC BY-NC-SA | competency-model.yaml + cka-ckad-coverage-matrix.md |
| I-18 | Fine-grained skill checklist | ckad-exercises | MIT | Coverage audit of the family catalog (checklist only; surface forms denylisted) |

## J.2 Content reused

| Item | Source repository | Source path | License | Reason | Modification | Attribution requirement |
|---|---|---|---|---|---|---|
| C-1: CKA and CKAD competency statements (domain titles, weights, competency text) | cncf/curriculum @ `f6c7667265fef850daaf93b4e19e919552c67d8c` | `CKA_Curriculum_v1.35.pdf`, `CKAD_Curriculum_v1.35.pdf` | **CC-BY 4.0+** (repository README) | The public competency standard is the construct KOPS measures | Transcribed verbatim into YAML; KOPS-assigned stable ids added; no text altered | Credit "CKA/CKAD Curriculum v1.35, Cloud Native Computing Foundation", link to the source and the license, and indicate changes (the id assignment). Present in the `competency-model.yaml` header; to be repeated in `THIRD_PARTY_NOTICES.md` at release. |

## J.3 Code proposed for reuse

**None proposed.** The candidates below were evaluated, and all are recommended for **independent reimplementation**. The reason is either that the fragment is small enough that reuse saves little, or that the source is not license-compatible.

| Candidate | Source path | License | Evaluation | Decision |
|---|---|---|---|---|
| Solution parser for `ssh node … exit` blocks + heredoc dedent | grindxhq-cka `cmd/test-runner/main.go` (`parseSolution`, `detectHeredoc`) | Apache-2.0 | KOPS uses structured solution helpers (`kops_node_exec`) instead of parsing prose | Not needed |
| Self-test driver loop | grindxhq-cka `cmd/test-runner/main.go` | Apache-2.0 | KOPS runtime is Python; the logic is simple and differs substantially (gateway path, negative control, digest) | Reimplement |
| Kubeconfig server rewrite for in-network clients | grindxhq-cka `internal/cluster/bastion.go` | Apache-2.0 | ~20 lines of trivial logic | Reimplement |
| Bastion + ssh key distribution to kind nodes | grindxhq-cka `internal/cluster/bastion.go` | Apache-2.0 | KOPS bakes sshd into a derived node image instead of apt-installing at runtime | Reimplement differently |
| Minimal validator executor | grindxhq-cka `internal/validator/validator.go` | Apache-2.0 | KOPS needs typed checks, tri-state results, settle and locations | Reimplement |
| Any provisioning script, check or YAML | k16s, ck-x, ckad-2026, ckad-dojo | PolyForm NC / BSL / GPL / CC BY-NC-SA | License-incompatible with the proposed Apache-2.0 KOPS core | **Prohibited** |
| Any file | ckad-exams | unlicensed | No rights granted | **Prohibited** |
| Task text, solutions, validators | all eight | — | Clean-room rule (brief §4) plus contamination | **Prohibited** |

**If a reuse is approved later,** add a row with all six mandatory fields:

| Source repository | Source path (@commit) | License | Reason for reuse | Modification | Attribution requirement |
|---|---|---|---|---|---|
| … | … | … | … | … | … |

Also: add the license text and notice to `THIRD_PARTY_NOTICES.md`, add a header to each derived file, and list the file in `metadata/provenance.yaml → copied_code` of any affected scenario.

## J.4 Ideas rejected (and why)

| Rejected idea | Seen in | Reason |
|---|---|---|
| Partial-credit weighted score as the primary metric; "pass at 66%" | grindxhq, ck-x, ckad-dojo, cka-hand-on-lab | Contradicts the frozen KOPS principle (binary scenario PASS). It hides failures of required behaviour. |
| Graders executed where the candidate works, or visible to them | ck-x, ckad-2026, ckad-exams, ckad-dojo | An agent will read or alter graders. KOPS isolates the verifier. |
| Grading a different location from the one the candidate edits | grindxhq (host vs bastion) | Invalid measurement. KOPS criteria declare a location. |
| Verifiers that re-apply candidate files, or apply the reference solution | ckad-exams | Grades files, not state, and one case is vacuous. KOPS grades live state only. |
| Control plane on the host; no per-task reset | k16s | Violates R1 (resettable units) and makes a failed task contaminate later ones. |
| Privileged LXC workers as the B2 design | k16s | Adds nothing over kind-node fidelity, with weaker isolation (backend-design.md §4). |
| k3s/k3d as the Kubernetes distribution | ck-x | Not kubeadm-shaped. Lacks CKA-relevant component layout. |
| Denylist or pattern-based cleanup | grindxhq, ckad-dojo | Incomplete (grindxhq) and destructive (dojo). KOPS uses destroy/snapshot or verified namespace reset. |
| Spec-only grading of NetworkPolicy, Ingress, Gateway, HPA | most repos | Rewards plausible YAML over working systems. KOPS uses behavioural invariants. |
| Keyword-heuristic parsing of verifier output; positional matching | ckad-dojo | Non-deterministic mapping of results to criteria. |
| Runtime downloads (apt, stable.txt, GitHub CRDs, Bitnami charts) | grindxhq, k16s, ck-x, ckad-dojo, ckad-exams | Breaks reproducibility. KOPS is pinned and offline. |
| Solutions or near-solutions in user-visible fields | grindxhq (API), k16s (hints), ck-x (API), ckad-* | Leaks to agents. |
| Timeouts shorter than a check's own polling; no exec timeouts | k16s; ck-x | Converts slow-correct into FAIL, or hangs evaluation. |
| Telemetry enabled by default | ck-x | Unacceptable for controlled experiments. |
| Human-oriented UI (desktop, VNC, timers) | all P0 | Out of scope. KOPS is agent-first. A human observer terminal is optional later. |
| LLM-as-judge for correctness | (none; brief constraint) | Deterministic state verification is possible for all planned families. |
| Unified CKA+CKAD score | (brief constraint) | Profiles are reported separately. |

## J.5 Repositories that must remain read-only

All reference repositories under `references/` are **read-only inputs**:

| Repository | Path | Additional restriction |
|---|---|---|
| grindxhq-cka | `references/p0/grindxhq-cka` | — |
| k16s | `references/p0/k16s` | Do not run its provisioning on shared lab hosts (it modifies host kernel, network and hostname) |
| ck-x | `references/p0/ck-x` | If ever run: `TRACK_METRICS=false`, block outbound traffic |
| ckad-2026 | `references/p0/ckad-2026` | **Q01–Q16 quarantined** (no reading by scenario authors) |
| ckad-dojo | `references/p0/ckad-dojo` | **Entire repo and git history quarantined as a content source.** It may be read only by the contamination-scan tool (as a negative corpus) and by auditors |
| cka-hand-on-lab | `references/p1/cka-hand-on-lab` | — |
| ckad-exams | `references/p1/ckad-exams` | Unlicensed: no copying of any file |
| ckad-exercises | `references/p1/ckad-exercises` | Its surface forms are denylisted |

**Verification:** `git status --porcelain` was empty in all eight repositories after the audit on 2026-09-26. Recommended enforcement: mount `references/` read-only in any CI or agent container (`:ro`), and add a CI check that fails if KOPS files match quarantine-corpus n-grams (contamination-denylist.yaml).
