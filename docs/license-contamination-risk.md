# License / Contamination Risk Matrix (E)

**Status: engineering assessment, not legal advice.** Items marked ⚖️ should be confirmed with the university's legal or tech-transfer office before any KOPS release.

---

## 1. Matrix

| Repo | License (verified) | Code reuse into KOPS core | Idea/design reuse | Contamination risk | Quarantine | Decision |
|---|---|---|---|---|---|---|
| grindxhq-cka | Apache-2.0. © 2026 grindxhq. No NOTICE file. | **Permitted** with license copy, change notices and attribution | ✅ | Low–medium. Generic, public; no dump or killer.sh markers. | No | Ideas adopted. Code reuse *possible* but **not planned by default** (reuse-register.md). |
| k16s | PolyForm Noncommercial 1.0.0 | ❌ Derived code would carry the NC restriction and the Required Notice. That is incompatible with a permissive KOPS release and blocks industry users. | ✅ Ideas and architecture only | Low–medium. Public; solutions in hints. | No | Architecture reference only. |
| ck-x | BSL 1.1 + Additional Use Grant (personal/educational/research/non-production). **MIT until `b837387` (2026-05-09)**. | ❌ BSL-encumbered: no hosted service, no commercial production. MIT-era snapshot exists ⚖️. | ✅ | Medium. killer.sh **UI** clone ("killer-sh-clone-webapp"), public tasks. No question-copy fingerprints. | No | Architecture reference only. Telemetry must be disabled if it is ever run. |
| ckad-2026 | GPL-3.0 | ❌ Copyleft would force KOPS core under GPL. The license chain is also doubtful for Q01–Q16 ⚖️. | ✅ Topic level only | **Medium overall; HIGH for Q01–Q16** (recall-list lineage shared with ckad-dojo sim4) | **Q01–Q16** | No code. No text. Topic labels only, all of which are already in the public curriculum. |
| ckad-dojo | CC BY-NC-SA 4.0 (paraphrased license text) | ❌ NC + SA, and incompatible with GPL, Apache and MIT. The licensor also cannot license killer.sh-derived content. | ✅ Architecture from code reading only | **HIGH.** Verbatim killer.sh "CKAD Simulator Kubernetes 1.34" in git history (`ce200ed`/`5646e61` → deleted in `2b839f8`). killer.sh-derived legacy scoring, manifests and templates at HEAD, used as a fallback. Recall-sourced sims (sim4, sim10). | **Entire repo as a content source, including its git history** | Architecture reference only. Never vendor, mirror or submodule it. |
| cka-hand-on-lab | MIT. © 2025–2026 Simon Balazs. | Permitted with notice | ✅ | Low–medium. AI-assisted (Claude co-author trailers). | No | Ideas only. Weak verifiers make its code unattractive. |
| ckad-exams | **None.** README MIT badge, but no LICENSE file in the tree or in history, which means all rights reserved ⚖️. | ❌ Not licensed | ⚠️ Describe patterns in our own words only | Low–medium. AI-generated (Task Master/Gemini). | No | **No reuse of any artefact.** Cite only. Optionally ask the author to add a license and record the reply. |
| ckad-exercises | MIT. © 2018 Dimitris-Ilias Gkanatsios. | Legally permitted | ✅ As a checklist | **HIGH** memorization (7 years of forks and mirrors) | No (legal), but **surface forms denylisted** | Coverage checklist plus contamination canary only. |
| CNCF curriculum (cncf/curriculum @ `f6c7667`) | CC-BY 4.0+ (repo README) | Text transcription with attribution (reuse-register C-1) | ✅ **Primary competency source** | none (it is the competency definition) | No | Transcribed into `competency-model.yaml` with SHA-256 of the PDFs. |

## 2. License compatibility for the KOPS release

| Option | KOPS license | Compatible with ideas from all repos? | Compatible with grindxhq/MIT code reuse? | Consequence |
|---|---|---|---|---|
| A | **Apache-2.0** | Yes: ideas are not copyrightable | Yes | Permissive, includes a patent grant, and suits academic plus industry adoption. |
| B | MIT | Yes | Yes (Apache code needs its NOTICE/licence kept) | Similar to A, with no patent clause. |
| C | GPL-3.0 | Yes | Yes | Would *allow* ckad-2026 code, but that code is unattractive and its chain is doubtful. It deters industry evaluation. |
| **Recommendation** | **A (Apache-2.0)** | | | Keep KOPS core free of NC, SA, BSL and GPL code. The reuse register (reuse-register.md) is the gate. |

## 3. Contamination: threat model

KOPS measures operational competency. Contamination inflates scores through **memorized surface forms** rather than skill. There are three vectors:

1. **Proprietary exam content.** This means real CKA/CKAD items, recalled items and killer.sh simulator items. These are *forbidden* inputs.
   - Found: ckad-dojo (git history plus HEAD legacy) and ckad-2026 Q01–Q16 (recall lineage).
   - Handling: **quarantine**. Nothing from these paths enters KOPS; they are used only as a *negative corpus* for similarity scanning.
2. **Public practice material that is memorized** (ckad-exercises, and to a lesser degree all public repos). This is legal, but KOPS scenarios that resemble it measure recall.
   - Handling: **denylist plus similarity warnings plus seeded parameters.**
3. **KOPS itself leaking into training data after publication.**
   - Handling: keep a **private held-out split**, meaning scenarios never published, run only by the lab. Rotate seeds per benchmark release. Publish the scenario *schema and families* openly and the held-out *instances* never. This is a decision for later (§6, Q3).

## 4. Controls (all automated in lint, and all required before `status: validated`)

| Control | Mechanism | File |
|---|---|---|
| Schema constants | `metadata.provenance.copied_question: const false`, `authored_clean_room: const true` | scenario.schema.json |
| Provenance record | Competency source (verbatim public text), design references *with license and use type*, upstream docs consulted, authoring method, contamination review sign-off | provenance.schema.json |
| Token denylist | killer.sh fingerprints, quarantined-repo code idioms, ckad-exercises canary tokens | [`contamination-denylist.yaml`](contamination-denylist.yaml) |
| Similarity scan | Word 8-gram overlap: against the **quarantine corpus** fail at 5% or more; against the **comparison corpus** warn at 15% or more | contamination-denylist.yaml `similarity` |
| Seeded variants | Names, ports and values rendered per trial seed; the published seed list is fixed per release | scenario.schema.json `task.parameters` |
| Clean-room authoring rule | Scenario authors write from the curriculum competency and kubernetes.io docs. They do **not** open quarantined paths. Reference notes in `docs/references/` are the only artefacts that cross over, and they contain no task prose. | this document |
| Reviewer sign-off | `contamination_review.reviewer` + date, required | provenance.schema.json |

**Notes on the audit itself.**
- The quarantined killer.sh file was only inspected for identification (title line, size, marker counts, commit SHAs).
- Audit notes paraphrase titles, list only generic topic labels for quarantined items, and reproduce no prose.
- Denylist tokens are recorded because detection requires them.

## 5. Residual risks

| Risk | Level | Mitigation |
|---|---|---|
| Public-domain operational patterns overlap with memorized content regardless of authoring (e.g. "fix a Service selector") | Medium, unavoidable | Families are curriculum-level. Instances vary by seed. We measure a **memorization control**: compare model pass rates on canonical-form vs. seeded-variant instances of the same family. A large gap flags memorization. This is an extra analysis for the research question. |
| An LLM-assisted authoring tool regurgitates memorized exam content | Medium | `authoring.method: human-original-llm-assisted` must be declared. Similarity scan plus reviewer. |
| The license status of ckad-exams could change | Low | Irrelevant, since nothing is used. |
| The CK-X MIT-era snapshot might tempt reuse | Low | The reuse register requires an explicit PI decision plus legal confirmation ⚖️. |

## 6. Decisions requested

1. **Q1.** Confirm that KOPS core will be released under **Apache-2.0**.
2. **Q2.** Confirm the quarantine of **ckad-dojo (entire repository and history)** and **ckad-2026 Q01–Q16**, including that they are *not even used as problem-family evidence*. The catalog lists them only under `quarantined_topic_sources` for audit completeness.
3. **Q3.** Should KOPS maintain a **private held-out scenario split** from v1.0 (recommended), or publish everything?
