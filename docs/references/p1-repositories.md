# P1 Reference Repositories: Audit Note

- **Audit date:** 2026-09-26
- **Scope:** three P1 (secondary) OSS repositories that were reviewed as read-only inputs to KOPS.
- **Method:** static reading only (`find`, `grep`, `sed`, `git log`, `git rev-parse`) of local clones under `/home/ubuntu/references/p1/`. No scripts were executed and no cluster was provisioned. We checked licenses with a file search and with a full `git log --all` search for any LICENSE path. We counted tasks from the files themselves, not from README claims.
- **Clean-room rule:** task titles in this note are paraphrased in 10 words or fewer. No question prose, solution YAML or validator code is reproduced.

| Repo | URL | Audited commit (full SHA) | License (verified) | Tasks | Contamination risk | KOPS usage decision |
|---|---|---|---|---|---|---|
| cka-hand-on-lab | https://github.com/simonbbbb/CKA-Hand-on-lab | `6818f52d02b3302fb5ce797de25991ef2f9caec9` | MIT, `LICENSE` file, © 2025-2026 Simon Balazs | 47 YAML tasks (the README claims "55+") | Low–medium (AI-assisted, generic CKA lore) | **Ideas only.** No content reuse. |
| ckad-exams | https://github.com/mmularski/ckad-exams | `c2bf3c84e9aee51a1619c9c60f3b7bd535445785` | **None.** No LICENSE in the tree or anywhere in history; the README MIT badge links to a missing file | 30 | Low–medium (AI-generated, generic CKAD) | **No reuse** of any kind. Related-work citation only. |
| ckad-exercises | https://github.com/dgkanatsios/CKAD-exercises | `d7b9a5c28b2ff2d8a8fab5524569956f21aaa1b4` | MIT, `LICENSE` file, © 2018 Dimitris-Ilias Gkanatsios | 152 Q&A items | **High** (heavily memorized) | Coverage checklist plus contamination canary/denylist only. |

None of the three repositories contains killer.sh fingerprints: no `/opt/course`, no planet-named namespaces (neptune, saturn, pluto, …), and no `holy-api`.

---

## A. cka-hand-on-lab

### 1. Architecture overview

This is a Rust terminal UI, the binary `cka-lab` v2.0.0 (`Cargo.toml`), built with ratatui, crossterm, serde_yaml and clap. Around it sits a legacy layer of about 1,700 lines of Bash (`setup.sh`, `setup/*.sh`). The main parts:

- **Content:** `tasks/<NN_domain>/<id>.yaml` holds 47 tasks, validated in principle by `tasks/schema.json`. Solutions are in `solutions/<domain>/`, and the legacy v1 READMEs and solutions are in `0N_*/`.
- **Code:** `src/main.rs` (CLI and event loop), `src/app.rs` (state and exam logic), `src/task/{loader,verifier}.rs`, and `src/ui/*.rs` (screens).
- **Coverage:** CKA only. The five domains are hard-coded with blueprint weights 10/15/20/30/25 (`DOMAIN_MAP` in `src/task/loader.rs`).
- **Provenance:** v2 was generated with AI assistance. Commits `4505da1` and `a0aeb3c` carry `Co-Authored-By: Claude Opus 4.7`, and `docs/superpowers/specs/2026-05-04-cka-lab-v2-design.md` is a design spec from the Claude Code "superpowers" plugin.
- **Tests:** there is no CI, no `tests/` directory, and no `#[test]` anywhere.

### 2. Runtime lifecycle

1. **Discovery.** clap parses `--path` and `--exam`. `TaskLoader::load_domains` walks the five fixed folders and parses the YAML files in filename order. Solution files are read eagerly and inlined. A parse error aborts startup.
2. **Setup.** The TUI does not perform setup. The user runs `setup.sh` (installs minikube and kubectl, starts minikube) or the per-domain `setup/0N_setup_*.sh` by hand. `setup_script` in the task YAML is metadata that nothing executes.
3. **Verify.** Pressing `v` runs `sh -c <verify_command>` synchronously with no timeout. The result is a substring match on stdout, scored 100 or 0. Progress is kept in an in-memory map and lost on exit.
4. **Reset.** The TUI has no reset. `setup/reset_lab_environment.sh` deletes and recreates minikube.
5. **Exam mode.** A 120-minute wall-clock timer runs over all 47 tasks. `v` toggles a self-declared "answered" flag and runs no checks. The score is the number of flags set, and 66% or more is a pass. Task `weight` is not used.

### 3. Scenario/task representation

Each task is one YAML file.

- **Required fields:** `id` (pattern `(sto|wrk|net|trb|arc)-NNN`), `domain` (enum), `title`, `description` (markdown), `difficulty`, `time_estimate` (`Nmin`), `weight` (1–20), `hints` (exactly 3).
- **Optional fields:** `tags`, `exam_tips`, `setup_script`, `verify_script`, `verify_command`, `verify_expected`, `solution_files`, `prerequisites`.

The schema is **not enforced**. The loader uses permissive serde deserializers: hints may be strings, maps or null; block scalars are accepted; difficulty falls back to a default. As a result, tasks that violate the schema load silently. Examples: `time_estimate: 6` without "min", and `weight: 30`, which exceeds the maximum of 20.

### 4. Environment abstraction

There is none. The code has no kubeconfig or context handling, and the environment is single-node minikube (qemu2 or docker driver) despite the README claiming "any cluster". Five tasks need node access: trb-008, trb-009, trb-012, arc-004 and arc-005. Two of those, trb-009 and trb-012, assume a second node `worker01` that minikube does not provide. Some images use floating tags, and some manifests are pulled from remote URLs.

### 5. Verification model

Each task has a single kubectl jsonpath command whose output must contain a substring. The checks are deterministic in form but weak:

- **Always pass:** arc-004..007 have an empty command and an empty expected value, so they **always pass**.
- **Near-vacuous:** six tasks expect `"."`, so any output containing a period passes.
- **Checks that don't match the task text:**
  - trb-011 checks a different PVC and namespace than its description names.
  - trb-009 inspects the first node in the list rather than the broken worker.
- **Faults never injected:** trb-008, trb-009 and trb-012 describe node-level faults that nothing sets up.

### 6. Reset/cleanup model

The only reset recreates the whole cluster. It deletes namespace names from v1 (`*-test`) that do not match the v2 task namespaces (`networking`, `troubleshooting`, …). There is no per-task cleanup, and nothing verifies that a reset succeeded.

### 7. Useful for KOPS

- The idea of one schema-backed manifest per task with domain-prefixed IDs and blueprint weights.
- Separate slots for setup, verify and solution. A `prerequisites` field for ordering tasks.
- A three-level progressive hint structure. This is useful for a human-practice mode but must not be shown to agents.
- A list of fault archetypes worth building properly in KOPS: a static-pod flag regression, kubelet client cert expiry, a CNI config CIDR drift, a StorageClass provisioner mismatch, a Service selector mismatch, a missing ConfigMap reference, and a bad rollout image.
- A reminder to cover 2025-blueprint topics: Gateway API, Pod Security Admission, Helm/Kustomize and HPA behavior.

### 8. Should NOT be copied

- Any task description, hint, exam tip or solution file.
- Single-field substring verifiers, and in particular empty or `"."` expectations.
- A self-graded exam mode.
- A `setup_script` field that never runs.
- Verification without a timeout.
- Hard-coded host paths (for example `/Users/…/CKA_LAB` in `setup/verify_solutions.sh`), the minikube/qemu2 coupling, floating image tags, and remote manifest URLs.

### 9. License implications

MIT (© 2025-2026 Simon Balazs). Reuse would be legally permitted with the notice retained. AI co-authorship does not change the license, but it weakens any "exam-realistic, human-authored" claim, and much of the content is broken or unverifiable anyway. Decision: **ideas only**. Cite it as related work and vendor no files.

### 10. Recommended adaptation pattern

Re-derive the fault archetypes from the public CKA curriculum and the Kubernetes docs, and implement them clean-room in KOPS's scenario schema. For each scenario:

- a strict schema, validated in CI;
- executed setup and fault-injection hooks;
- multi-assertion checks against live state, with per-check timeouts;
- per-scenario reset plus a check that the reset worked;
- multi-node kind or kubeadm environments for the node-level cases.

Treat this repository's task list as a topic checklist, not a source.

### Appendix: task inventory (47)

| id | Paraphrased title | Domain | Node? |
|---|---|---|---|
| sto-001 | Create a StorageClass | Storage | N |
| sto-002 | Create hostPath PersistentVolume | Storage | N |
| sto-003 | Create PersistentVolumeClaim | Storage | N |
| sto-004 | Pod mounting a PVC | Storage | N |
| sto-005 | Dynamic provisioning via default class | Storage | N |
| wrk-001 | Deployment with rolling-update strategy | Workloads & Scheduling | N |
| wrk-002 | Perform rolling image update | Workloads & Scheduling | N |
| wrk-003 | Roll back deployment | Workloads & Scheduling | N |
| wrk-004 | Configure pod via ConfigMap and Secret | Workloads & Scheduling | N |
| wrk-005 | HPA basics | Workloads & Scheduling | N |
| wrk-006 | Node affinity and taints scheduling | Workloads & Scheduling | N |
| wrk-007 | Container requests and limits | Workloads & Scheduling | N |
| wrk-008 | HPA with scale-up stabilization | Workloads & Scheduling | N |
| wrk-009 | Multi-metric HPA | Workloads & Scheduling | N |
| net-001 | ClusterIP and NodePort Services | Services & Networking | N |
| net-002 | NetworkPolicy ingress and egress | Services & Networking | N |
| net-003 | Ingress path-based routing | Services & Networking | N |
| net-004 | Troubleshoot service connectivity | Services & Networking | N |
| net-005 | Multi-port Service | Services & Networking | N |
| net-006 | CoreDNS custom domain rewrite | Services & Networking | N |
| net-007 | Create a GatewayClass | Services & Networking | N |
| net-008 | Gateway plus HTTPRoute path routing | Services & Networking | N |
| net-009 | Gateway TLS termination and redirect | Services & Networking | N |
| net-010 | Default-deny ingress policy | Services & Networking | N |
| net-011 | Cross-namespace pod allow policy | Services & Networking | N |
| net-012 | Egress to multiple destinations | Services & Networking | N |
| trb-001 | Fix image pull error pod | Troubleshooting | N |
| trb-002 | Fix under-resourced pod | Troubleshooting | N |
| trb-003 | Fix service selector mismatch | Troubleshooting | N |
| trb-004 | Fix pod missing ConfigMap | Troubleshooting | N |
| trb-005 | Fix deployment update strategy | Troubleshooting | N |
| trb-006 | Diagnose failure from container logs | Troubleshooting | N |
| trb-007 | Troubleshoot pod DNS resolution | Troubleshooting | N |
| trb-008 | Repair broken kube-apiserver static pod | Troubleshooting | Y |
| trb-009 | Recover node with expired kubelet cert | Troubleshooting | Y (multi-node) |
| trb-010 | Fix ImagePullBackOff deployment | Troubleshooting | N |
| trb-011 | Fix StorageClass provisioning failure | Troubleshooting | N |
| trb-012 | Repair CNI cross-node networking | Troubleshooting | Y (multi-node) |
| arc-001 | Create namespaced RBAC Role | Cluster Arch, Install & Config | N |
| arc-002 | Bind Role to user | Cluster Arch, Install & Config | N |
| arc-003 | Create a CRD | Cluster Arch, Install & Config | N |
| arc-004 | Author kubeadm config file | Cluster Arch, Install & Config | Y (file only) |
| arc-005 | Document etcd backup/restore | Cluster Arch, Install & Config | Y (doc only) |
| arc-006 | Write Helm values file | Cluster Arch, Install & Config | N |
| arc-007 | Build Kustomize overlay | Cluster Arch, Install & Config | N |
| arc-008 | Enforce Pod Security via namespace labels | Cluster Arch, Install & Config (CKS-adjacent) | N |
| arc-009 | Fix Pod Security violation | Cluster Arch, Install & Config (CKS-adjacent) | N |

---

## B. ckad-exams

### 1. Architecture overview

A folder-convention repository with no runtime code. It contains two CKAD practice sets, `ckad-tasks/exam-0/` and `ckad-tasks/exam-1/`, with 15 tasks each. Each task has `prep/`, `task/task-description.md` and `answer/` (`solution.*` and `validation.sh`). Everything is Bash, YAML and Markdown.

The repository was **AI-generated**:

- `.taskmaster/config.json` configures Task Master AI with `gemini-cli` / `gemini-2.5-pro`.
- `.taskmaster/docs/ckad_prd.txt` is a PRD that calls the tasks "authentic CKAD exam tasks".
- `.cursor/rules/*.mdc` are authoring rules, and `.cursor/mcp.json` wires in the task-master MCP (its API keys are placeholders).
- Commit `d8914fe` is titled "ai rulesets".
- The whole history is 12 commits between 2025-07-18 and 2025-07-29.
- The README still contains a template clone URL (`your-username/ckad-ai`).

There is no CI.

### 2. Runtime lifecycle

1. The candidate reads the task description.
2. The candidate writes manifests into `prep/`. A `.gitignore` there keeps them out of git.
3. The candidate runs `./answer/validation.sh`. It applies `prep/` itself, then applies it again with `--force`. It waits for readiness, asserts, and prints pass or fail.
4. On a pass, the script deletes the task's resources and namespace.

There is no timer, no orchestration across tasks, and no aggregation of scores.

### 3. Scenario/task representation

There is no machine-readable schema. Each description contains Markdown sections: Points (3–8), Scenario, Preparation, Requirements, Deliverables and Validation. Each task has its own namespace, `exam-{0,1}-task-NN`. Point totals are 87 for exam-0 and 103 for exam-1, but the validators are binary.

### 4. Environment abstraction

The user brings a single cluster. The README suggests minikube with Calico. Tasks also need Helm, jq and Docker or Podman. The Helm tasks pull `bitnami/postgresql` from the public Bitnami repo. Two tasks touch the node: e0-13 needs a host container runtime to get a custom image into the cluster, and e1-03 uses a hostPath volume.

### 5. Verification model

Bash scripts run with `set -e` and grade the **files the student submitted**, which the validator applies itself, rather than live state the agent leaves behind. Assertions include:

- pod phase polling (10 tries, 1 s apart);
- `kubectl logs` grep;
- jsonpath field checks;
- `kubectl exec` connectivity probes, with positive and negative clients for NetworkPolicy;
- `auth can-i`;
- `helm get values | jq`.

Defects:

- **Answer leakage:** `exam-1/task-14…/answer/validation.sh` applies the **reference solution**, so the task always passes.
- **Coupled tasks:** e0-15 reuses e0-14's namespace and Helm release.
- **Unobservable skill:** e0-11 cannot observe the skill it claims to test.
- **Negative-evidence check:** e1-09 passes when certain error strings are absent from the logs.
- **Timing fragility:** checks rely on fixed sleeps and short timeouts.

### 6. Reset/cleanup model

On a pass, the validator deletes that task's namespace and resources. On a fail it leaves everything in place. There is no global reset, and nothing verifies cleanup.

### 7. Useful for KOPS

These are conceptual patterns only, and must be re-expressed independently:

- NetworkPolicy grading with both an allowed-client probe and a denied-client probe.
- Mechanism-specific assertions, for example confirming a change was made through Helm release values rather than a direct edit.
- Behavioral checks (logs, connectivity) in addition to spec checks.
- A per-task namespace naming convention.

All four patterns are generic and widely known. KOPS does not need this repository to adopt them.

### 8. Should NOT be copied

- **Everything.** No file, description, prep manifest, solution or validator.
- Also not to be emulated:
  - validators that apply submitted or reference files;
  - answers stored beside tasks, where an agent can read them;
  - coupling between tasks;
  - negative-evidence checks;
  - sleep-based timing;
  - dependence on public chart repositories.

### 9. License implications

There is **no LICENSE file in the working tree or anywhere in git history.** A `find` for license, copying and notice files returned nothing, as did `git ls-files`, `git log --all -- LICENSE*`, and a search of the file lists of every commit. The README's MIT badge and its "see LICENSE" link point to a file that does not exist, so they do not grant a license. The default is therefore **all rights reserved**. GitHub's terms allow viewing and forking on the platform only, not redistribution or derivative works. AI authorship may affect copyrightability, but that is legally unsettled and must not be relied on.

**Decision: no reuse.** This covers verbatim copying, adaptation and translation into KOPS's format. The repository may be cited as related work. Reuse could only be reconsidered if the author adds an explicit license and KOPS keeps a record of that change.

### 10. Recommended adaptation pattern

None from this source. The CKAD topics it covers are standard curriculum items. Author equivalent KOPS scenarios directly from the CNCF CKAD curriculum and the Kubernetes documentation, with no reference to this repository's wording, resource names or scripts. Grade live state and keep solutions outside the agent's workspace. If a KOPS scenario happens to cover the same topic, record in its provenance field that it was authored independently.

### Appendix: task inventory (30)

| id | Paraphrased title | Pts | CKAD domain (best guess) | Node? |
|---|---|---|---|---|
| e0-01 | Pod env from ConfigMap | 4 | Env, Config & Security | N |
| e0-02 | Mount ConfigMap as volume | 4 | Env, Config & Security | N |
| e0-03 | Secret values as env vars | 4 | Env, Config & Security | N |
| e0-04 | Liveness/readiness probes | 6 | Observability & Maintenance | N |
| e0-05 | Container requests and limits | 6 | Env, Config & Security | N |
| e0-06 | Scale a Deployment | 6 | Deployment | N |
| e0-07 | Expose app via Service | 6 | Services & Networking | N |
| e0-08 | Sidecar multi-container pod | 7 | Design & Build | N |
| e0-09 | Fix broken Deployment | 8 | Observability & Maintenance | N |
| e0-10 | Restrict backend with NetworkPolicy | 7 | Services & Networking | N |
| e0-11 | Namespace context switching practice | 3 | kubectl fluency (not graded meaningfully) | N |
| e0-12 | ServiceAccount with Role binding | 6 | Env, Config & Security | N |
| e0-13 | Build custom image, run pod | 7 | Design & Build | Y (runtime) |
| e0-14 | Install Helm release with values | 6 | Deployment | N |
| e0-15 | Upgrade Helm release values | 7 | Deployment | N |
| e1-01 | Batch Job processing | 5 | Design & Build | N |
| e1-02 | Scheduled CronJob | 6 | Design & Build | N |
| e1-03 | PV/PVC with hostPath pod | 7 | Design & Build | Y (hostPath) |
| e1-04 | Pod securityContext settings | 6 | Env, Config & Security | N |
| e1-05 | ResourceQuota and LimitRange | 7 | Env, Config & Security | N |
| e1-06 | Expose via Ingress | 7 | Services & Networking | N |
| e1-07 | PodDisruptionBudget | 6 | Deployment (edge of curriculum) | N |
| e1-08 | Init container preparation | 7 | Design & Build | N |
| e1-09 | Diagnose app from logs, fix config | 8 | Observability & Maintenance | N |
| e1-10 | CRD plus custom resource | 8 | Env, Config & Security | N |
| e1-11 | Advanced ConfigMap volume usage | 7 | Env, Config & Security | N |
| e1-12 | Advanced Secret env usage | 7 | Env, Config & Security | N |
| e1-13 | Ambassador multi-container pattern | 8 | Design & Build | N |
| e1-14 | Cross-namespace NetworkPolicy | 7 | Services & Networking | N |
| e1-15 | Rolling update strategy tuning | 7 | Deployment | N |

---

## C. ckad-exercises

### 1. Architecture overview

Ten Markdown files, `a.core_concepts.md` through `j.podman.md`, containing 152 question headings, each with a collapsible answer. There is no code, CI or automation. The repository has been community-maintained since 2018: 275 commits from about 176 authors, with the latest merge at PR #398. The domain headings follow the **2018 CKAD blueprint** (Core Concepts 13%, Pod Design 20%, …), not the current five domains. `README.md` lists files a–i and omits `j.podman.md`.

### 2. Runtime lifecycle

None. A reader works through each file, runs the commands on their own cluster, and expands the answer to compare.

### 3. Scenario/task representation

The structure is `# Domain (weight%)`, then an optional `## Subtopic`, then `### Question`, then the collapsible answer. Each file opens with breadcrumb links to kubernetes.io docs. Questions within a file build on each other, reusing the same resource names.

### 4. Environment abstraction

Any cluster, driven by imperative kubectl. Some items assume the playground node names `node01` and `controlplane`, a local registry, podman, and internet access (the Bitnami chart repo and an author-published demo image).

### 5. Verification model

None. The reader checks their own work against the revealed answer.

### 6. Reset/cleanup model

Occasional inline "delete what you created" steps. Nothing systematic.

### 7. Useful for KOPS

- **Coverage checklist.** Its fine-grained items map onto CKAD sub-competencies. Use them to audit `competency-model.yaml` for gaps, for example: rollout pause/resume and revision history, Job completions/parallelism/deadline, CronJob history limits, typed Secrets, ServiceAccount token generation, LimitRange versus ResourceQuota interplay, `kubectl cp`, and image build/push/pull-secret flows.
- **Contamination canary.** This is among the most-forked CKAD resources, so models have very likely memorized its surface forms. The tokens below should go into KOPS's contamination denylist. Treat them as tokens only, and check them in the context of resource names and literal values.
  - **Namespaces:** `mynamespace`, `myns`, `limitrange`, `secret-ops`, `one`
  - **Pods, workloads and services:** `nginx1`, `nginx2`, `nginx3`, `busybox2`, `consumer`, `foo`, `my-app-svc`, `pi`, `private-reg`, `private-reg-container`
  - **Configuration objects:** `myrq`, `config`, `options`, `anotherone`, `cmvolume`, `mysecret`, `mysecret2`, `ext-service-secret`, `myuser`
  - **Storage objects:** `myvolume`, `mypvc`
  - **CRD and Helm:** `operators.stable.example.com`, `operator-sample`, `Operator` (as a CRD kind), `chart-test`, `mynode`, `myvalues`
  - **Literal values and label strings:**
    - config values `lala`, `lolo`, `var5`–`var9`, `val5`–`val9`;
    - labels and annotations `app=v1`, `app=v2`, `tier=web`, `owner=marketing`, `accelerator=nvidia-tesla-p100`;
    - port `6262`;
    - image `dgkanatsios/simpleapp`;
    - image tag sequence `nginx:1.18.0` → `nginx:1.19.8` → `nginx:1.91` → `nginx:1.19.9`, and `perl:5.34`.
- **Doc-breadcrumb idea:** map each KOPS domain to the kubernetes.io pages allowed during the exam.

### 8. Should NOT be copied

- Question wording, answer snippets and resource names (see the token list above).
- The step-chained question sequences.
- The 2018 domain names and weights.
- Even where MIT permits reuse, any KOPS task resembling these items measures recall, not operational skill.

### 9. License implications

MIT (© 2018 Dimitris-Ilias Gkanatsios). Community PRs are inbound under the same terms by convention. Reuse is legally permitted with the copyright and permission notice retained. KOPS declines content reuse for **validity reasons**, not legal ones. The token list above is a factual list of identifiers used to avoid overlap. It is not an expressive reproduction.

### 10. Recommended adaptation pattern

- Build a coverage matrix that maps each exercise group to KOPS competency IDs, recording counts only.
- Add the token list to the contamination scan, alongside n-gram overlap checks against a quarantined copy of this corpus.
- Author KOPS scenarios with non-generic, scenario-specific names and multi-step operational context. Avoid the single-command drill form.
- Optionally keep a small "memorization control" split: KOPS-authored items deliberately phrased in this repository's style, used to measure recall-driven inflation. Label it clearly as analysis-only.

### Appendix: task inventory (per-file group counts)

| File | Count | Groups (count) | Current CKAD domain (best guess) |
|---|---|---|---|
| `a.core_concepts.md` | 18 | Namespaces, pod basics, quota YAML, exec/logs/describe, env | Mixed / kubectl fluency |
| `b.multi_container_pods.md` | 2 | Multi-container; init container | Design & Build |
| `c.pod_design.md` | 52 | Labels & Annotations (13); Pod Placement (4); Deployments (19); Jobs (9); CronJobs (7) | Deployment; Design & Build; placement is CKA-leaning |
| `d.configuration.md` | 30 | ConfigMaps (8); SecurityContext (2); Requests/limits (1); LimitRanges (3); ResourceQuotas (3); Secrets (9); ServiceAccounts (4) | Env, Config & Security |
| `e.observability.md` | 8 | Probes (4); Logging (1); Debugging (3) | Observability & Maintenance |
| `f.services.md` | 10 | Services, endpoints, NetworkPolicy, Ingress | Services & Networking |
| `g.state.md` | 6 | Volumes, PV/PVC, copy files | Design & Build |
| `h.helm.md` | 10 | Chart lifecycle, repos, values | Deployment |
| `i.crd.md` | 4 | CRD definition and objects | Env, Config & Security |
| `j.podman.md` | 12 | Image build, registry, pull secrets | Design & Build |
| **Total** | **152** | | |

---

## Cross-cutting conclusions

1. None of the P1 repositories provides a verification model that KOPS can use as-is. KOPS keeps its own design: live-state, multi-assertion, timeout-bounded checks; executed setup and fault-injection hooks; per-scenario verified reset; and solutions kept outside the agent's view.
2. License posture:
   - cka-hand-on-lab (MIT): ideas only.
   - ckad-exams (unlicensed): no reuse at all.
   - ckad-exercises (MIT): checklist and denylist only.
3. The P1 repositories describe node-level CKA troubleshooting but cannot run it. KOPS needs multi-node environments with node access to cover those scenarios for real.
