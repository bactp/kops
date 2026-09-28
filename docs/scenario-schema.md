# KOPS Scenario Schema — Proposal (F)

Status: **PROPOSED `kops/v1alpha1`**. Not frozen until architecture review.
Machine-readable schemas:

| File | Validates | Notes |
|---|---|---|
| [`../schemas/scenario.schema.json`](../schemas/scenario.schema.json) | `scenario.yaml` | JSON Schema 2020-12. Profile/domain/competency constraints are generated from [`competency-model.yaml`](competency-model.yaml). |
| [`../schemas/criteria.schema.json`](../schemas/criteria.schema.json) | `verify/criteria.yaml` | Typed, deterministic check primitives. |
| [`../schemas/provenance.schema.json`](../schemas/provenance.schema.json) | `metadata/provenance.yaml` | Clean-room record. `copied_question` is `const: false`. |

Worked, validated example: [`examples/kops-net-service-endpoint-repair-001/`](examples/kops-net-service-endpoint-repair-001/).

> **Change vs. the brief.** The brief asked only for `scenario.schema.json`. I split it into three schemas because the criteria and provenance files have different reviewers and life-cycles: the verifier engine owns criteria, and the contamination review owns provenance. Each can then be validated and version-bumped independently. `scenario.yaml` keeps a summary of both (`expected_invariants`, `metadata.provenance`) so that a reader of one file still sees the contract.

---

## 1. Design inputs from the audit

Each schema feature below answers a concrete defect or a good idea found in the reference repositories. File-level evidence is in `docs/references/*.md`.

| Observation in reference repos | Schema response |
|---|---|
| grindxhq-cka validators pass on the **initial** state (s5-11, s2-15). No negative control exists in its E2E runner. | `setup.confirm.must_fail` is **required and non-empty**. After setup, the goal invariants must evaluate to *fail* before any agent acts. |
| CK-X swallows setup failures: the `for` loop ignores exit codes and the exam is still `READY`. | `setup.confirm.must_pass` plus runner semantics. A setup error or a failed confirmation makes the trial **INVALID**, never scored. |
| CK-X exposes grader filenames through its API. ckad-exams stores `answer/` next to the task, and one validator applies the reference solution itself. grindxhq returns `solution` through the API. | `reference.exposure: const "hidden"`. The runner never mounts `reference/`, `verify/` or `scenario.yaml` into the agent workstation. Only `task.md` plus `agent_context` is rendered to the agent. |
| grindxhq grades host files while the user works in the bastion (s5-05/06/09/15/16). | Criteria have an explicit **location**: `k8s.*` goes to the API as verifier-admin; `node.*` goes to a named node; `artifact.location` is `workstation` or `node`. There is no implicit "host". |
| String-contains over whole YAML dumps; `verify_expected: "."`; empty-string verifiers that always pass (cka-hand-on-lab arc-004..007). | A typed check vocabulary (`k8s.field` with JSONPath and an operator, `k8s.can_i`, `net.http` …). The raw-shell `script` check requires a written `justification`. |
| Pod-phase checks with no retry (grindxhq: 5 s, no polling). "Restart in last 60 s" checks (CK-X). | Per-criterion `settle` gives bounded polling until pass or deadline. `stability` gives an explicit sampled window. Both are declared and recorded, not hidden `sleep`s. |
| Denylist reset coupled to content (grindxhq). No reset on FAIL (ckad-exams). Jumphost state leaking across exams (CK-X). | `backend.isolation` plus `reset.strategy` plus `reset.verify_baseline`. A baseline digest mismatch quarantines the backend instance. |
| Unpinned Kubernetes, `:latest` images, runtime downloads (grindxhq, CK-X, ckad-exams). | `backend.kubernetes_version` is required. Backends pin node images by digest (see backend-design.md). Scenario lint forbids untagged or `:latest` images in fixtures. |
| Free-text categories: 29 distinct spellings in grindxhq. Domain folders hard-coded in cka-hand-on-lab. | Enumerated `domain` and `primary_competency` per profile, **schema-enforced consistency** (a competency must belong to its domain). |
| Task and verifier drift (cka-hand-on-lab trb-011 checks a different PVC name than the text). | `task.parameters` render into *all* files from one source. The linter cross-checks invariants against criteria. The self-test runs the reference solution. |
| Good idea (grindxhq): hidden setup and validation vs. visible task. Separate solution. E2E "apply solution → validate". | Kept, and extended with negative control, `negative_solutions` (verifier mutation tests) and reset verification. |
| Good idea (CK-X): step-level graders with an exit-code contract and weights. | Kept as **criteria**, but used for diagnosis only. PASS is binary (`all-required`). No weights enter the primary metric. |

---

## 2. Directory layout of one scenario

```
<scenario-id>/
├── scenario.yaml            # this schema (hidden from agent)
├── task.md                  # ONLY agent-visible text (templated with {{params}})
├── setup/
│   └── setup.sh             # idempotent; runs as verifier-admin on the runner (or on nodes)
├── verify/
│   ├── verify.sh            # thin wrapper: `kops verify --scenario . --trial $TRIAL_DIR` (human convenience)
│   ├── criteria.yaml        # executable invariants (criteria.schema.json)
│   └── checks/              # optional scripts for `type: script` criteria
├── fixtures/                # manifests/files applied by setup (pinned images only)
├── reference/
│   ├── solution.sh          # hidden oracle; structured targets, see §6
│   └── wrong-*.sh           # optional negative solutions (must FAIL)
└── metadata/
    └── provenance.yaml      # provenance.schema.json
```

**Why keep both `verify.sh` and `criteria.yaml`?**

| | Option A: `verify.sh` is the verifier (CK-X / ckad-exams style) | Option B: `criteria.yaml` executed by a KOPS engine; `verify.sh` is a thin wrapper |
|---|---|---|
| Flexibility | Maximal | Bounded by the check vocabulary. There is an escape hatch (`script`) |
| Per-criterion diagnostics | Ad-hoc parsing of stdout | Native: each criterion has an id, a failure_class and evidence |
| Auditability / review | Must read bash | Declarative and diffable. The reviewer sees the invariant, not the implementation |
| Determinism controls (timeouts, settle, location) | Re-implemented per script, often forgotten | Centralized and uniform |
| Anti-patterns seen in audit | All of them occurred | Prevented structurally |
| **Recommendation** | | **B**. `verify.sh` stays so that a human can run `./verify/verify.sh` against a live environment, as the brief's layout expects. |

---

## 3. `scenario.yaml` field reference

Legend: **R** = required.

### 3.1 Identity and lifecycle

| Field | R | Meaning |
|---|---|---|
| `apiVersion: kops/v1alpha1`, `kind: Scenario` | R | Schema version. |
| `id` | R | `^(cka\|ckad\|kops)-<slug>-NNN$`. It is stable forever and never reused. `kops-` is used for dual-profile scenarios. |
| `revision` | R | Bumped on any change to agent-visible text, initial state or verifier semantics. **Results are comparable only within the same `(id, revision)`**, and the result record also stores the content digest. |
| `status` | R | `draft` → `validated` (self-test green) → `frozen` (in a released benchmark version; immutable) → `retired`. |
| `family_id` |  | Link to `problem-family-catalog.yaml` (`PF-XXX-NNN`). |
| `difficulty.level` |  | 1 single-step · 2 diagnosis or multi-step · 3 multi-component or system-level. Used for stratified reporting only. |

### 3.2 `profiles` — independent CKA and CKAD mappings

```yaml
profiles:
  cka:  {enabled: true,  domain: troubleshooting,     primary_competency: CKA-TRB-05,  mapping_rationale: "..."}
  ckad: {enabled: true,  domain: services-networking, primary_competency: CKAD-SNW-02, mapping_rationale: "..."}
```

Schema-enforced rules:

- At least one profile is enabled.
- An enabled profile has **exactly one** `domain` and **exactly one** `primary_competency`, and the competency must belong to that domain (generated `oneOf` from `competency-model.yaml`).
- A disabled profile must not carry a domain or competency, which avoids "ghost" mappings.
- `secondary_competencies` is informational and **never** used for scoring or coverage counts.
- `mapping_rationale` is mandatory. It is reviewed in the acceptance checklist, because the *primary-competency* decision is the main threat to construct validity.

No field anywhere combines profiles. Reports are generated per profile.

### 3.3 `backend`

| Field | R | Meaning |
|---|---|---|
| `class` | R | `kind` (object-level) · `kind-node` (kind plus node exec: systemd, kubelet, containerd, static pods, etcd, PKI) · `vm` (full Linux VMs: kubeadm install/upgrade/join, OS prep, HA). See backend-design.md. |
| `kubernetes_version` | R | Minor or patch version. It must match an available backend image. The v1 benchmark targets **1.35** to match curriculum v1.35. |
| `topology` | R | Control-plane and worker counts. |
| `features` |  | Required add-ons provided by the backend *profile*, not by scenario setup: `networkpolicy`, `metrics-server`, `default-storageclass`, `gateway-api`, `ingress-controller`, `audit-log`, … This keeps setup scripts small and add-on versions pinned centrally. |
| `isolation` | R | `cluster`: fresh cluster or snapshot per trial. `namespace`: shared cluster, and the scenario touches only `namespaces` (proven by the reset self-test). |

### 3.4 `task` — the only agent-visible content

- `statement_file` (normally `task.md`) is rendered with the trial's parameters. It contains no hints about the verifier, no mention of criteria ids, and no solution.
- `parameters` holds **seeded variants**: names, ports and choices. They serve two purposes:
  1. Contamination resistance: surface forms differ from anything memorized.
  2. Variance estimation across isomorphic instances.

  The seed is part of the trial key and recorded. Primary experiments use a fixed, published seed list, so that every agent sees identical instances.
- `agent_context` holds the facts every agent receives in the same format: kube context, default namespace, accessible nodes, working directory.

### 3.5 `interfaces`

- `allowed` and `forbidden` come from a closed vocabulary: `kubectl, kubernetes-api, kubernetes-mcp, shell, file-read, file-write, helm, kustomize, ssh, systemctl, journalctl, crictl, etcdctl, etcdutl, kubeadm, openssl, podman, curl, internet`. The runner materializes them as the workstation tool set and PATH, not as prompt text.
- `agent_identity` is the Kubernetes identity in the agent kubeconfig: `cluster-admin`, `namespace-admin`, or `custom-rbac` plus a file. It is **always distinct from the verifier identity**, so the API audit log attributes every mutation.
- `node_access` is `none`, `ssh` (exam-like: the workstation can `ssh <node>`) or `exec` (runtime-mediated).

### 3.6 `initial_state`, `constraints`, `budgets`

- `initial_state.faults[]` is a typed fault inventory (`category`, `layer`). It is used for failure analysis ("which fault classes do SLMs miss?") and for coverage reporting. It is hidden from the agent.
- `constraints[]` holds rules the agent must obey. Each declares `enforced_by`: `rbac`, `tooling`, or `invariant` (then it must reference a guard invariant). **A constraint that nothing enforces is a schema error.** This prevents unverifiable instructions.
- `budgets` holds `max_steps`, `max_wall_seconds`, `per_action_timeout_seconds` and `max_output_bytes_per_action`. An experiment may override them globally, but only uniformly across agents.

### 3.7 `expected_invariants`

This is the human-readable contract. Every entry has:

- `kind`: `goal` (desired end state) or `guard` (must not be violated: collateral damage, anti-shortcut, "do not recreate the Service").
- `required`: PASS needs all required invariants to hold.

At least one required goal invariant is mandatory (schema `contains`). The linter checks that each invariant has at least one criterion and that the `required` flags agree.

### 3.8 `setup`

- `script` is idempotent bash that runs as verifier-admin on the runner (or on nodes via `executes_on`).
- `confirm.must_fail` lists goal invariants that must *fail* after setup. This is the **negative control**, and it is **required**.
- `confirm.must_pass` lists guards or preconditions that must hold after setup.
- After a successful confirm, the runner snapshots the **post-setup baseline** that `k8s.unchanged` and `node.file.unchanged_since` compare against.

### 3.9 `verification`

- `engine: kops-verifier/v1`, `criteria_file`, `entrypoint`.
- `pass_rule: all-required` is a constant. A criterion `status: error` (verifier or infrastructure fault, e.g. the probe pod can't pull its image) makes the trial **INVALID**. It is rerun and reported separately, never counted as the agent's FAIL.
- `settle` is the bounded convergence window for criteria with `settle: true`.
- `credentials: verifier-admin` is a constant. The verifier never uses the agent's identity or workstation.

### 3.10 `reset`

`destroy-cluster`, `snapshot-restore`, `namespace-delete` or `script`. With `verify_baseline: true`, the runner compares a canonical state digest (see runtime-architecture.md §6) against the pre-setup baseline. A mismatch quarantines the instance, which makes a reset leak visible instead of silently contaminating the next trial.

### 3.11 `reference`

`solution` is required and hidden. `negative_solutions` is optional: plausible wrong fixes that must FAIL. An example is fixing only the selector but not the targetPort. These are **verifier mutation tests**, and they are the cheapest way to catch vacuous or under-specified criteria.

### 3.12 `metadata`

`kubernetes_version`, `authors`, `created`, `competency_model`, and `provenance` (`file`, `copied_question: false`, `authored_clean_room: true`, both schema constants).

---

## 4. Criteria vocabulary (`criteria.schema.json`)

| Type | Location | Deterministic basis | Typical use |
|---|---|---|---|
| `k8s.exists` | API | object presence or absence | created or deleted objects |
| `k8s.field` | API | JSONPath + operator (`eq, ne, in, regex, exists, gte, subset…`) | spec values, labels, env |
| `k8s.count` | API | count with an optional field filter | N ready pods |
| `k8s.condition` | API | `.status.conditions[type]` | Available, Ready, Complete |
| `k8s.rollout_complete` | API | generation == observedGeneration ∧ updated == ready == replicas | rollouts and rollbacks |
| `k8s.endpoints` | API | EndpointSlice ready count on a port | Service repair |
| `k8s.can_i` | API | SubjectAccessReview allow/deny | RBAC least privilege (allow **and** deny matrix) |
| `k8s.unchanged` | API | hash of selected JSONPaths vs. post-setup baseline | guards: "don't touch the pod template" |
| `net.http` / `net.tcp` | ephemeral probe pod (pinned image) | status code, body regex, or blocked-after-timeout with N attempts | Service, Ingress, Gateway, NetworkPolicy (positive **and** negative probes) |
| `net.dns` | probe pod | resolution result | CoreDNS repair |
| `node.exec` | node via backend | argv exit code and stdout regex | `crictl`, `kubeadm certs check-expiration` |
| `node.systemd` | node | unit active and enabled | kubelet or containerd repaired **and persistent** |
| `node.file` | node | exists, sha256, regex, mode, unchanged | static-pod manifests, kubelet config |
| `artifact` | workstation or node | verifier-side validator script | etcd snapshot validity (`etcdutl snapshot status`), a produced manifest |
| `stability` | any | nested check sampled N times over W seconds | "no restarts for 30 s" after probe fixes |
| `script` | runner | exit 0 / 1 / other = pass / fail / error | escape hatch, **with justification** |

Tri-state results: `pass | fail | error`. Only `pass`/`fail` are agent outcomes. `error` is an infrastructure outcome.

`failure_class` labels (`goal-not-reached`, `partial-configuration`, `wrong-target`, `collateral-damage`, `constraint-violation`, `not-persistent`, `unstable`) feed the diagnostic taxonomy. They never feed the primary metric.

---

## 5. Validation pipeline (lint)

1. **Render** the scenario for the default seed plus N sampled seeds. Template tokens make raw files invalid YAML, which I confirmed while building the example, so the schema is validated on *rendered* documents. This also proves every variant is well-formed.
2. JSON-Schema-validate `scenario.yaml`, `criteria.yaml` and `provenance.yaml`.
3. Cross-file rules, which JSON Schema cannot express:
   - every invariant is implemented by at least one criterion, with no orphan criteria and consistent `required` flags;
   - `setup.confirm.*` ids exist;
   - every `constraints[].invariant` exists and is a `guard`;
   - all referenced files exist, and nothing under `reference/` or `verify/` is referenced from `task.md`;
   - fixtures use only images pinned by tag+digest; no `:latest`;
   - `backend.class` is compatible with the criteria (no `node.*` checks on a `kind` scenario);
   - `interfaces.allowed` is compatible with `backend.class` (e.g. `ssh` needs `kind-node` or `vm`).
4. Contamination scan of `task.md`: fingerprint denylist plus n-gram overlap against the quarantined reference corpus (see license-contamination-risk.md §4).

I checked these negative cases against the schema, and all were rejected: a domain/competency mismatch, `copied_question: true`, an exposed solution, no profile enabled, a disabled profile carrying a domain, no required goal invariant, a list of primary competencies, an empty `must_fail`, and a `../` path traversal.

---

## 6. Reference solution format

grindxhq parses prose solutions with `ssh node … exit` blocks. That is clever but brittle. For KOPS I propose:

| | Option A: plain `solution.sh` run on the runner, with helper functions `kops_node_exec <node> <<'EOF' … EOF` | Option B: YAML list of `{target, script}` steps |
|---|---|---|
| Authoring ergonomics | High (it's just bash) | Medium |
| Runs through the same path as the agent | Yes, if the helpers use the same gateway | Yes |
| Recommendation | **A** | |

Option A has lower friction. The helpers (`kops_node_exec`, `kops_ws_exec`) route through the **same tool gateway the agent uses**, which fixes grindxhq's "solution runs on host, user works in bastion" blind spot.

---

## 7. Open questions for review

1. **Dual-profile ids.** Is the `kops-` prefix acceptable for dual-profile scenarios, or do you prefer an owner prefix (`cka-`/`ckad-`) even when both profiles are enabled?
2. **Difficulty.** Keep the three-level author-assigned scale, or derive difficulty empirically after pilot runs (e.g. from frontier pass rates)? I recommend the author scale for stratification now, with empirical calibration later.
3. **Partial-credit reporting.** The criteria give a natural "fraction of required criteria met". I propose reporting it only as a **secondary diagnostic**, labelled as such, never averaged into PASS rates.
