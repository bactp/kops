# KOPS — Kubernetes Operations Benchmark (W1-KOPS, Track A2)

KOPS is a research-grade, **executable** benchmark for Kubernetes AI agents, grounded in the public CKA and CKAD competency specifications (CNCF curriculum v1.35).

An agent under test works inside a real Kubernetes environment. An independent, deterministic verifier then checks the resulting state and returns PASS or FAIL. The agent's own claim of success is never enough.

```
Scenario → initial state / injected fault → agent observes and acts (via Tool Gateway)
         → environment changes → deterministic verifier → PASS / FAIL (per profile: CKA, CKAD)
```

## Status

**Phase: architecture proposal, awaiting review.** No runtime code or scenarios exist yet, by design.

- Start here: [`docs/00-architecture-proposal.md`](docs/00-architecture-proposal.md). It summarizes deliverables A–J and lists the decisions requested.
- Schemas (proposed `kops/v1alpha1`): [`schemas/`](schemas/)
- Worked scenario example (schema-validated, not executable yet): [`docs/examples/`](docs/examples/)

## Principles (frozen)

- Separate **CKA** and **CKAD** profiles. There is no unified certification score.
- Evaluation unit: **Agent × Scenario × Trial**. Primary metric: **scenario PASS/FAIL** from observable state invariants. No LLM judge.
- Only observable behaviour is captured: tool calls, results and environment mutations. Chain-of-thought is never requested.
- Clean room: no exam dumps, recalled questions, or killer.sh material. Every scenario has a provenance record.
- Every scenario passes an automated self-test before any agent sees it.

## Reference material

`../references/` holds external repositories used as **read-only** inputs. See [`docs/reference-inventory.md`](docs/reference-inventory.md) and [`docs/reuse-register.md`](docs/reuse-register.md). Some of them are quarantined, as described in [`docs/license-contamination-risk.md`](docs/license-contamination-risk.md).
