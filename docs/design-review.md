# KOPS Track A2 — Design Review (pre-runtime)

- **Date:** 2026-10-01
- **Scope:** Track A2 only: an exam-like, executable environment that benchmarks AI agents against the CKA/CKAD competency specifications (curriculum v1.35). Building or fine-tuning models (Track A1) is out of scope here. Section H only lists what A2 must guarantee so that A1 can use it later.
- **Repo state reviewed:** `b173d62` plus the uncommitted `decision-log.md` and review-status notes.
- **Verdict:** the design is on target for A2 and its verification ideas are strong. Nothing runs yet. A few exam-fidelity gaps exist (§C). The first runtime should be the smallest slice that behaves like one exam task: assign, inject, work, submit, grade.

> This replaces an earlier draft that reviewed the repo against the broader W1 brief. That draft wrongly cut the CKA/CKAD profile structure, provenance and contamination controls. For A2 these are core.

---

## A. Repository reconstruction

| Artifact | State |
|---|---|
| 28 committed files (about 7.6k lines) | Markdown, YAML, CSV, JSON only. |
| Executable code, tests, CI | **None.** |
| Runnable scenarios | **None.** The example `kops-net-service-endpoint-repair-001` has `scenario.yaml`, `criteria.yaml` and `provenance.yaml` only. `task.md`, `setup.sh`, fixtures and `reference/` are referenced but absent. |
| Schemas (scenario, criteria, provenance) | Valid schemas. The example validates against all three **after rendering `{{params}}`** (re-checked today with `jsonschema` 3.2, which handles draft-07 only. The 2020-12 claim is untested here). `criteria.yaml` is not valid YAML before rendering. |
| Uncommitted | `decision-log.md`; review-status lines. Decisions #1, #3, #4, #5 approved; #2 deferred; #6–#16 open. |
| Host | Docker 29.6, `kubectl`, `kubeadm`, `uv`. **`kind` not installed.** No GPU. The default kubectl context is a **real cluster** and other kubeconfigs are in `$HOME`. |

| Layer | Status |
|---|---|
| Audit of 8 CKA/CKAD simulator repos | Documentation; evidence, not run. |
| Competency model, 72-family catalog, coverage matrices | Designed only. |
| Scenario, criteria, provenance schemas | Drafted, schema-valid. |
| Backends A / B1 / B2 | Designed only. All numbers are unmeasured estimates (spikes S-1, S-2 not run). |
| Runtime (gateway, scaffold, verifier, recorder, selftest) | Designed only. |
| Vertical slice (10 + 2 scenarios) | Designed only. |

Hypothetical until run: kind with a pinned 1.35 image, kindnet NetworkPolicy enforcement, audit-log identity attribution, recoverability of B1 node faults, stability of probe pods.

---

## B. How the design maps to an exam

The goal is an environment that behaves like taking CKA/CKAD: receive a task, work in a terminal against real clusters, submit, get graded afterwards.

| In the real exam | In the KOPS design | Where |
|---|---|---|
| Question is shown to the candidate | Rendered `task.md` plus `agent_context` is the only thing the agent sees | scenario-schema §3.4 |
| Pre-built broken or empty cluster | Backend provisions it; `setup.sh` injects the fault as verifier-admin | backend-design §2–3, runtime §1 |
| Candidate works in a terminal with `kubectl`, `ssh`, `vim` | Workstation container with pinned CLIs; `ssh <node>` for node scenarios; `read_file`/`write_file` replace editors | backend-design §5, runtime §3.3 |
| Candidate can't see the grader | Verifier, criteria and reference are never mounted; separate verifier identity | schema §1, backend R3 |
| "Done" = stop working | `submit`, step budget or wall clock ends the episode | runtime §3.3 |
| Graded after the exam | Verifier runs after the workstation is frozen and checks cluster state | runtime §2 |
| Results per question | `trial.json`, `verifier.json`, `trace.jsonl` | runtime §5 |
| Next candidate gets a clean environment | Reset plus baseline-digest check; failed reset quarantines the instance | runtime §2.1 |
| Per-domain weights (CKA: Troubleshooting 30%, Architecture 25%, …) | Per-domain and per-competency reporting; optional weighted summary labelled "not a certification score" | runtime §5 |

---

## C. Gaps between the design and a real CKA/CKAD exam

These are the places where the design differs from the exam in ways that affect what the benchmark measures.

1. **No documentation access.** The real exam allows kubernetes.io docs (and helm, gateway-api docs). The design sets `internet` as forbidden. Agents then work closed-book, which is harder than the exam and penalises small models. Options: (a) offline mirror of the permitted docs inside the workstation, (b) closed-book as a stated variant, (c) both as a recorded experiment variable. Needs a decision. This is the largest fidelity gap.
2. **One task per trial, not a multi-task session.** The exam is about 15–20 tasks in 2 hours with time shared across tasks. The design runs one scenario per trial, which is fine for measurement. A "session" mode (a set of tasks with a shared clock) can be added later. Report as a known limitation.
3. **Multiple clusters and context switching.** The exam gives several clusters and tells the candidate to switch context for each task. The schema has a single `kube_context`. Whether to model this is open. Context mix-ups are a real exam failure mode.
4. **Binary PASS vs. weighted exam scoring.** The exam gives partial credit per task. The design reports binary PASS as primary and partial credit as a labelled secondary (decision #15). I support that for agent evaluation, but "exam-equivalent score" cannot be claimed.
5. **No TTY.** No interactive `vim` or `kubectl edit`. The design routes edits through `write_file` and `kubectl patch`/`apply`. Document it. It changes what is measured.
6. **kind is not an exam cluster.** Exam clusters are kubeadm VMs. kind nodes are containers: no own kernel, no distro-package `kubeadm upgrade`, no real reboot. The design acknowledges this and lets B1 cover about 11 of 16 system-level families. Five `vm` families (cluster upgrade, install/join, OS prep, HA, resource pressure) remain **uncovered** until B2. CKA Architecture (25%) is hit hardest.
7. **No agent-side failure taxonomy, and the metrics "invalid action" and "recovery" are undefined.** The design records trace and verifier failure classes, but not the agent-side classes (tool-use, execution, recovery). They are derivable from the trace (§F).

---

## D. Does the design meet the A2 objectives?

| Objective | Verdict |
|---|---|
| Exam-like assign / inject / submit / grade flow | **Designed, complete.** |
| Verification by cluster state, not text | **Designed, strong** (negative control, null agent, wrong-fix mutation tests, oracle through the agent's own permissions). |
| CKA and CKAD kept separate and mapped to the curriculum | **Designed, strong** (schema-enforced competency mapping, per-profile reporting). |
| Clean-room content and contamination control | **Designed, strong.** Becomes essential once A1 trains on K8s data. |
| Resettable, reproducible environment | **Designed, unproven** (needs spike S-1). |
| System-level CKA coverage | **Partial.** B1 only; B2 deferred (§C.6). |
| Exam fidelity (docs, contexts, sessions) | **Gaps** (§C.1–C.3). |
| Running anything | **No.** |

The design overall is sound. The risk is in building too much before one scenario runs end to end, not in direction.

---

## E. Component necessity

| Component | Why it exists (A2) | If removed | Verdict |
|---|---|---|---|
| Scenario spec + render with seed | Reproducible instances; contamination resistance | Nothing is repeatable | Keep |
| Declarative criteria | Auditable, uniform determinism, per-criterion evidence | Verification becomes bash | Keep; implement a small check vocabulary first |
| Negative control + `selftest` | Trust in every scenario | A scenario may pass on the broken state | Keep, build first |
| Guards | Catch delete/recreate/over-privilege shortcuts | Shortcuts count as PASS | Keep |
| INVALID vs FAIL | Separate infra faults from model failures | Results polluted | Keep |
| Tool Gateway (budgets, allowlist, recording) | Same interface and limits for every model | Models are not comparable | Keep |
| Trace recorder | Trajectory analysis | Only a pass bit | Keep |
| Workstation container | Exam-like terminal; isolation from host | Agent runs next to real kubeconfigs | Keep (needed for safety, §I) |
| Provenance and contamination scan | Clean-room claim; train/test hygiene for A1 | Cannot defend the benchmark | Keep, implement after the first scenarios run |
| Held-out split | Fine-tuned models must not see the test set | Contaminated results | Keep (decision #12 → accept) |
| CKA/CKAD profile mapping | The benchmark's meaning | No "CKA/CKAD" claim | Keep |
| 72-family catalog | Corpus planning | Nothing runtime | Keep as docs; not a runtime input yet |
| B1 `kind-node` | Troubleshooting and component faults | CKA Troubleshooting cannot be covered | Keep; build after the `kind` slice works |
| B2 `vm` | Upgrade, HA, OS prep, reboot | Those families stay uncovered | Deferred (agreed) |
| Warm pool, scheduler concurrency | Throughput | Slower runs | Defer |
| API audit log | Authoritative mutation record | Mutations inferred from commands plus final-state diff | Keep in design; implement with S-1 |
| Track S (third-party agents) | Compare agent products | Nothing in A2 core | Defer |
| Mixed-effects stats, pass^k | Analysis | Nothing at runtime | Defer; store raw per-trial data |

---

## F. Architecture decision review (#1–#16)

| # | Decision | Verdict | Reason |
|---|---|---|---|
| 1 | B1 counts as system-level | **ACCEPT** | Good trade-off. Build after the `kind` slice. |
| 2 | B2 engine | **DEFER** | Agreed. Coverage reports must show the 5 `vm` families as uncovered. |
| 3 | Gateway/Ingress controller | **ACCEPT** | Single dual-mode controller. Choose it when the first Ingress/Gateway scenario is built, not before. |
| 4 | CNI | **ACCEPT** | Measure when the first NetworkPolicy scenario (S06) is built. |
| 5 | Pin 1.35 | **ACCEPT, verify first** | Confirm a `kindest/node` 1.35 image exists; otherwise pin the newest and record why. |
| 6 | Declarative verifier + thin `verify.sh` | **MODIFY** | Keep declarative. Start with `k8s.field`, `k8s.condition`/`rollout_complete`, `k8s.exists`, `k8s.count`, `k8s.unchanged`. Add `net.*`, `node.*`, `stability`, `artifact` when a scenario needs them. |
| 7 | Both Track M and Track S | **MODIFY** | Build Track M (runtime-driven Reference Scaffold) only. Track S later. |
| 8 | Python | **ACCEPT** | |
| 9 | Proposed layout | **MODIFY** | Create a directory only when code needs it (§G). Keep `scenarios/<id>/` flat. |
| 10 | Apache-2.0 | **ACCEPT** | |
| 11 | Quarantine scope | **ACCEPT** | Needed for the clean-room claim. |
| 12 | Held-out private split | **ACCEPT** | Required once A1 fine-tunes. Decide the split unit (scenario vs. family) before authoring many scenarios, since seeded variants of one family are not independent. |
| 13 | `kops-` prefix for dual-profile ids | **ACCEPT** | |
| 14 | Author-assigned difficulty 1–3 | **ACCEPT** | Calibrate empirically later. |
| 15 | Partial credit as labelled secondary | **ACCEPT** | |
| 16 | Mapping ambiguities (5 families) | **ACCEPT with review** | Construct validity. Review before freezing the first release, not before the first run. |
| new | Documentation access (§C.1) | **DECIDE** | Open: offline docs mirror, closed-book, or both as a variable. |
| new | Context-switch fidelity (§C.3) | **DECIDE** | Open: one or several kube contexts per task. |
| new | Do not store chain-of-thought | **MODIFY** | Store model messages as sent and received. Do not request reasoning. |
| new | Fresh cluster per trial as default | **MODIFY** | Prefer a reused cluster with namespace-per-trial plus a baseline digest check for `isolation: namespace` scenarios. Fresh cluster only for cluster-scoped faults. Speeds up iteration. |

---

## G. Proposed minimal architecture

The smallest thing that works like one exam question.

```
scenarios/<id>/ ──▶ Loader ──▶ Runner ──┬─▶ Backend (kind): cluster, namespace, fixtures, reset
 scenario.yaml                          ├─▶ Workstation + Tool Gateway ◀──▶ Agent (Reference Scaffold ⇄ model)
 task.md / setup / criteria / reference │         (budgets, allowlist, trace)
                                        ├─▶ Verifier (criteria.yaml, verifier identity)
                                        └─▶ Result recorder (trial.json, trace.jsonl)
```

- **Python package `kops`:** `scenario`, `backend_kind`, `gateway`, `scaffold`, `models`, `verifier`, `recorder`, `runner`, `cli`.
- **Layout:**
  ```
  pyproject.toml
  src/kops/…
  scenarios/<id>/{scenario.yaml,task.md,setup/,fixtures/,verify/criteria.yaml,reference/}
  experiments/<name>.yaml
  tests/
  results/                 # git-ignored
  docs/ schemas/           # existing
  ```
- **Backend `kind`:** creates a cluster with a **private kubeconfig** (never `~/.kube/config`), a namespace per trial, two identities (`verifier` cluster-admin, `agent` per scenario), and a canonical state snapshot for reset checks.
- **Workstation:** a container that holds only the allowed CLIs and the agent kubeconfig. For the very first spike a kubectl-only tool run on the runner (`shlex`, no `shell=True`, scrubbed env, explicit `KUBECONFIG`) is acceptable. A workstation container is required before enabling a shell tool or `ssh`.
- **Scaffold:** a fixed, versioned prompt plus an observe → command → output loop through an OpenAI-compatible client. One code path for every model.
- **Verifier:** evaluates `criteria.yaml` as `verifier` after the agent has finished. Any `error` makes the trial INVALID.

### Lifecycle

| Stage | Owner | What happens |
|---|---|---|
| LOAD | Loader | Read scenario, render seeded parameters, compute digest, build the agent view |
| PROVISION / RESET | Backend | Healthy cluster, fresh namespace, snapshot `S0`, environment fingerprint |
| SETUP | Backend + setup script | Inject the fault as verifier. Error → INVALID |
| READY | Runner + verifier | Setup confirm: goals FAIL, guards PASS (negative control). Take guard baselines |
| RUN AGENT | Gateway + scaffold | Loop until `submit`, budget or wall clock. Every step traced |
| VERIFY | Verifier | After the agent session ends |
| COLLECT RESULT | Recorder | Trial record, per-criterion results, trace, final-state snapshot |
| CLEANUP | Backend | Delete namespace; compare to `S0`; mismatch marks the cluster dirty |

Failures before RUN AGENT or after it (setup, confirm, verify, cleanup, harness crash) are INVALID. Model-caused outcomes (bad commands, timeouts, budget exhaustion) are FAIL.

### Agent loop

```
for step in 1..max_steps:
    reply  = model.generate(history)
    action = parse(reply)                       # command | submit | malformed
    malformed      → error observation, kind=parse_error
    not allowed    → policy observation, kind=policy_rejected
    otherwise      → run with timeout → ok | exec_error | timeout
    record(step); history += reply, observation
    stop on submit / budget / wall clock
```

Invalid commands consume a step and come back as ordinary observations. A timeout kills the process and returns a `TIMEOUT` observation. `submit` text is stored but never scored.

### Metrics derived from the trace (secondary to PASS/FAIL)

- **Invalid action:** parse error, policy rejection, or a kubectl syntax-class error. NotFound of a named object is not invalid. The stderr pattern list is versioned. It is a heuristic.
- **Recovery:** after an error step, a later successful step on the same resource kind/name before the next error; also episode-level "had an error and still PASS".
- **Interface errors** are reported separately from Kubernetes competence (important for small models).
- **Auto failure labels:** tool-use, execution, no-attempt, recovery, harness. Knowledge vs. reasoning requires manual annotation and is marked secondary.

### Minimum result record (`trial.json`)

Scenario id, revision, digest, seed and parameters; **profile(s) and competency ids** from the scenario; agent (model id as served, params, weights/adapter reference, scaffold version, prompt hash, tools); limits; environment fingerprint (Kubernetes and node-image digest, tool versions, KOPS git sha); outcome and invalid reason; termination; per-criterion verifier results; counts (steps, invalid actions, errors, recoveries, mutating steps); timings and tokens; the agent's claim; auto failure labels; reset status. One file per trial, plus `trace.jsonl`. No composite score.

---

## H. Constraints A2 places on the later model track (A1)

- Evaluation must run models through the same scaffold with only the weights (or adapter) changed.
- The held-out split and contamination scan must exist before any training data is generated from A2 scenarios.
- Seeded variants of one family are not independent. Split by family, not by seed.
- Decide what "meets CKA/CKAD standard" means before training. Candidate: a pass-rate threshold per domain, reported per profile. This is an A1 decision and is not specified in the repo today.

---

## I. First runnable slice and phase order

**Phase 1: pipeline proof (not a result).**
1. Install `kind`; confirm a 1.35 node image; use only a private kubeconfig. Refuse to run if the active context is not the KOPS kind cluster.
2. Author **one CKAD scenario** end to end. S03 (`kops-net-service-endpoint-repair-001`) is already half-drafted and dual-profile, so I would finish it: add `task.md`, fixtures, `setup.sh`, `reference/solution.sh` and the two wrong-fix scripts.
3. `kops selftest`: negative control; null agent FAIL; wrong-fix scripts FAIL; oracle PASS ×3; reset digest equals baseline.
4. Run two model agents through the scaffold (one frontier, one local), 3 trials each.

**Acceptance:** the scenario creates the same broken state on fresh namespaces; null FAILs and oracle PASSes; every step including failed commands is traced; the verifier decides independently of the claim; reset is clean; one table compares both models.

**Then:** Phase 2, S01–S08 on `kind`. Phase 3, the workstation container and S09–S10 on `kind-node`. Phase 4, pilot with 1 SLM + 1 frontier model (pipeline shake-down). Documentation-access and context-switch decisions (§C) must be made before Phase 2, since they change the task set and the tool set.

---

## K. Decisions of 2026-10-01 and the proposals that follow

**Decided** (see `decision-log.md`): offline docs mirror; simulated context switching; clean environment for every trial.

### K.1 Scoring proposal (open)

The exam scores each task by weight and gives partial credit. It passes at 66% overall. For agents, unrestricted partial credit can be gamed, so:

1. **Strict result (primary, unchanged):** scenario PASS/FAIL, all required criteria.
2. **Exam-style task score (second reported number, labelled "exam-equivalent, not a certification score"):**
   - Each *goal* criterion carries an author-assigned `weight`. Weights per scenario sum to 100.
   - Task score = sum of weights of passed goal criteria.
   - **Gating:** if any required *guard* fails (collateral damage, wrong-context mutation, delete/recreate, over-privilege), the task score is 0.
   - Weights are hidden and reviewed like the criteria. They never enter the PASS rule.
3. **Per-domain and per-profile score:** average task score within a domain, per profile. Profile score = domain scores weighted by the curriculum weights, shown only when every domain has enough scenarios (the design asks for at least 8 per domain per profile).
4. **"Meets the standard", by part:** a model meets the CKA (or CKAD) standard when the profile score is at least 66% **and** every domain is at least a floor. The floor is not defined by the exam and is a policy choice (proposal: 50%). Report each domain's score with a confidence interval, averaged over seeds and trials.
5. Never combine CKA and CKAD scores.

This extends decision #15: partial credit becomes a second reported number, not only a diagnostic. The strict PASS rate stays alongside it.

### K.2 Execution environment: where the runner and clusters live

Two roles must stay separate:

- **Runner (long-lived):** orchestrates trials, holds model API keys, runs the agent loop and the verifier, writes results.
- **Trial sandbox (one per trial, disposable):** the clusters, the agent's workstation and the docs mirror.

The agent's commands run inside the sandbox through the Tool Gateway. Model keys and results never enter the sandbox.

**Is "kind inside a pod" viable?** Yes, with conditions.

- kind needs a Docker daemon. Inside a pod that means Docker-in-Docker (privileged pod) or a runtime such as Sysbox. Cluster nodes then run inside the pod's Docker, so root in a node is not root on the Kubernetes host's Docker. That is a real containment benefit over running kind on the host.
- Costs and risks: privileged pods; nested cgroup v2 and overlayfs quirks; images must be preloaded in the sandbox image or a local registry, or each trial re-pulls everything; roughly 2–3 GiB RAM per cluster (unmeasured), more with several contexts; cluster create of about 30–60 s (unmeasured).
- **It must not run on the existing real cluster.** Agent-driven privileged pods next to production workloads defeat the isolation goal. A host cluster for trial pods would have to be dedicated and disposable.

**Recommendation:** define one **trial sandbox image** (Docker daemon + kind + pinned CLIs + docs mirror). Phase 1 runs it with `docker run --privileged` on a dedicated host or VM. The same image later runs as a Kubernetes Job on a dedicated cluster, which gives scale-out without redesign. The `Backend` interface hides the difference. Do not build the Kubernetes-hosted variant first.

### K.3 Context switching

A trial sandbox can create 2–3 small single-node kind clusters (target plus decoys) with one kubeconfig and several contexts. The task text names the context to use. The verifier checks the target cluster's goals and that the decoys are unchanged. Cost scales with the number of clusters, so `contexts` is a per-scenario parameter and most scenarios start with one.

### K.4 Docs mirror

A static build of the permitted documentation, pinned to the benchmark Kubernetes version, served inside the sandbox network. It is the only reachable host. The Kubernetes docs are CC-BY 4.0. The permitted set is a versioned list, and fetches are traced.

---

## J. Risks and open items

1. **Host safety.** The default kubectl context is a real cluster. Every subprocess must get an explicit `KUBECONFIG` and a scrubbed environment.
2. **`kind` not installed;** 1.35 image availability unverified.
3. **No GPU.** A local model means a small quantised model on CPU or a remote endpoint.
4. **Frontier model credentials** and model id are needed for Phase 1.
5. **Open decisions:** documentation access, context switching, split unit for held-out data, and the meaning of "meets the standard".
6. **Related work.** The audit covered human exam simulators only. SREGym, Kubeply and infraben.ch are not compared, so no novelty claim yet.
7. **Schema debt.** The schemas allow more than the runtime will read. Freeze them and add fields only when code uses them.

---

## L. Phase 1 status (2026-10-01)

Implemented and run: `src/kops/` (scenario, backend_kind, gateway, harness, models, verifier, recorder, runner, selftest, experiment, lint, cli); 25 unit tests plus 1 e2e test; scenario `kops-net-service-endpoint-repair-001`.

**Measured** (kind v0.33.0, node v1.35.8 pinned by digest, this host):
- Cluster create with cached images: about 30 s. Cold create including image download: 212 s. Delete: about 1.6 s.
- Memory of a single-node cluster: about 0.5 GiB (the design estimated 2–3 GiB).
- `kind load docker-image` fails with Docker 29's containerd image store. The backend loads single-platform archives instead.

**Selftest result** (3 parallel clusters): setup confirm holds for every run; null agent FAIL; wrong-fix-selector-only FAIL (endpoints and HTTP); wrong-recreate-service FAIL (UID guard only); oracle PASS ×3; every cluster destroyed; `~/.kube/config` unchanged.

**Harness check:** a scripted model produced a parse error, a policy rejection, an invalid kubectl command, a recovery and a mutation on a real cluster. All were traced and counted, and the trial still PASSed.

**Bug found by the real run:** `classify_command` took the value of `-n` for the kubectl verb, so mutating commands were not counted. Fixed, with a regression test.

**Not done / known gaps**
- No real model has run. No API key or local endpoint is configured on this host.
- The agent kubeconfig is a copy of the admin credentials. A distinct agent identity (needed for the audit log) is a TODO.
- Setup runs on the host with `bash`; the agent's kubectl runs on the host. The sandbox image (Docker + kind + CLIs in one container) from §K.2 is not built.
- Failed trials are slow (about 3 min) because each settling criterion waits its full 60 s. Settle once per trial instead.
- Images use tags, not digests. Lint does not yet enforce pinning.
- Fixture images are preloaded from the host's Docker cache, so the first run needs internet.
