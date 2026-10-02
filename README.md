# KOPS — Kubernetes Operations Benchmark (W1-KOPS, Track A2)

KOPS is a research-grade, **executable** benchmark for Kubernetes AI agents, grounded in the public CKA and CKAD competency specifications (CNCF curriculum v1.35).

An agent under test works inside a real Kubernetes environment. An independent, deterministic verifier then checks the resulting state and returns PASS or FAIL. The agent's own claim of success is never enough.

```
Scenario → initial state / injected fault → agent observes and acts (via Tool Gateway)
         → environment changes → deterministic verifier → PASS / FAIL (per profile: CKA, CKAD)
```

## Status

**Phase 1 (pipeline proof) is implemented for one scenario.** Everything else is still a design.

- Runs today: `kind` backend (one fresh cluster per trial, private kubeconfig), kubectl-only Tool Gateway, shell-loop agent over any OpenAI-compatible endpoint, null and oracle agents, a declarative verifier (5 check types), `selftest`, trial records and a comparison table.
- Scenario available: `kops-net-service-endpoint-repair-001` (CKA Troubleshooting / CKAD Services & Networking).
- Not built yet: workstation container, `kind-node` and `vm` backends, docs mirror, multi-context tasks, held-out split, contamination scanner, scoring beyond PASS/FAIL. See [`docs/design-review.md`](docs/design-review.md).
- Design entry point: [`docs/00-architecture-proposal.md`](docs/00-architecture-proposal.md). Decisions: [`docs/decision-log.md`](docs/decision-log.md).
- Schemas (proposed `kops/v1alpha1`): [`schemas/`](schemas/). Scenarios: [`scenarios/`](scenarios/)

```bash
uv venv --python 3.12 .venv && uv pip install -e ".[dev]"   # kind + kubectl 1.35 must be in ~/.local/share/kops/bin
.venv/bin/kops lint kops-net-service-endpoint-repair-001
.venv/bin/kops selftest kops-net-service-endpoint-repair-001
.venv/bin/kops run experiments/phase1-baselines.yaml
```

## Principles (frozen)

- Separate **CKA** and **CKAD** profiles. There is no unified certification score.
- Evaluation unit: **Agent × Scenario × Trial**. Primary metric: **scenario PASS/FAIL** from observable state invariants. No LLM judge.
- Only observable behaviour is captured: tool calls, results and environment mutations. Chain-of-thought is never requested.
- Clean room: no exam dumps, recalled questions, or killer.sh material. Every scenario has a provenance record.
- Every scenario passes an automated self-test before any agent sees it.

## Reference material

`../references/` holds external repositories used as **read-only** inputs. See [`docs/reference-inventory.md`](docs/reference-inventory.md) and [`docs/reuse-register.md`](docs/reuse-register.md). Some of them are quarantined, as described in [`docs/license-contamination-risk.md`](docs/license-contamination-risk.md).
