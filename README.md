# KOPS — Kubernetes Operations Benchmark (W1-KOPS, Track A2)

KOPS is a research-grade, **executable** benchmark for Kubernetes AI agents, grounded in the public CKA and CKAD competency specifications (CNCF curriculum v1.35).

An agent under test works inside a real Kubernetes environment. An independent, deterministic verifier then checks the resulting state and returns PASS or FAIL. The agent's own claim of success is never enough.

```
Scenario → initial state / injected fault → agent observes and acts (via Tool Gateway)
         → environment changes → deterministic verifier → PASS / FAIL (per profile: CKA, CKAD)
```

## Status

**v0.1 (in progress, deployed on the lab cluster): Practice mode and Playground on KubeVirt sandboxes, with a web dashboard and accounts.** See [`CHANGELOG.md`](CHANGELOG.md), the design in [`docs/simulator-design.md`](docs/simulator-design.md), the API in [`docs/platform-api.md`](docs/platform-api.md) and the runbook in [`docs/operations.md`](docs/operations.md).

- Platform: FastAPI backend (`src/kops/platform/`), static dashboard (`web/`), `KubeVirtProvider` (`src/kops/providers/kubevirt.py`), OIDC login with a bundled Keycloak (self-registration).
- Practice: pick a task, get a disposable Kubernetes cluster (about 2 minutes), work in a browser terminal like the exam (`base` then ssh to the node), CHECK with evidence per criterion, hints, solution, Next/Restart (about 40 seconds when the scenario's API-level reset is proven).
- Scenarios: 60 for CKA and CKAD; the catalogue shows only those validated on the KubeVirt sandbox (`catalog/available.txt`).
- Also available: the Phase 1 CLI on kind (`kops lint | selftest | run | lab`), which remains the quick way to author a scenario.
- Later releases: Mock Exam, docs mirror, editor, node-level scenarios, agent gateway (see the release plan).

```bash
# author or check a scenario on a laptop with docker + kind
uv venv --python 3.12 .venv && uv pip install -e ".[dev]"
.venv/bin/kops lint kops-net-service-endpoint-repair-001
.venv/bin/kops selftest kops-net-service-endpoint-repair-001
.venv/bin/kops lab up kops-net-service-endpoint-repair-001       # take the task yourself in the terminal
# run the platform tests
.venv/bin/pytest -q
# deploy: see docs/operations.md
```

## Principles (frozen)

- Separate **CKA** and **CKAD** profiles. There is no unified certification score.
- Evaluation unit: **Agent × Scenario × Trial**. Primary metric: **scenario PASS/FAIL** from observable state invariants. No LLM judge.
- Only observable behaviour is captured: tool calls, results and environment mutations. Chain-of-thought is never requested.
- Clean room: no exam dumps, recalled questions, or killer.sh material. Every scenario has a provenance record.
- Every scenario passes an automated self-test before any agent sees it.

## Reference material

`../references/` holds external repositories used as **read-only** inputs. See [`docs/reference-inventory.md`](docs/reference-inventory.md) and [`docs/reuse-register.md`](docs/reuse-register.md). Some of them are quarantined, as described in [`docs/license-contamination-risk.md`](docs/license-contamination-risk.md).
