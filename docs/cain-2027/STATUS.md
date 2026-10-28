# CAIN 2027: implementation status, pilots, and gaps

**Reviewed:** 2026-10-25 (branch `feat/cain-sources-sandbox-host`, 103 unit tests passing).
**Source plan:** [`HarnessWeaver_CAIN_2027_Coauthor_Plan.md`](HarnessWeaver_CAIN_2027_Coauthor_Plan.md).
**Purpose:** Separate what exists and runs today from what the paper plan assumes, fix the pilots, and list the remaining work in priority order. Update this file when evidence changes; it is the single status reference for the submission.

Status legend: **Done** = implemented and exercised with recorded evidence. **Partial** = implemented but not exercised end to end, or exercised only under an older contract. **Missing** = not implemented.

## 1. Plan concepts mapped to repository artifacts

The plan names five concepts. The repository realizes them inside HarnessSpec v0.2 plus companion files rather than as separate schemas. For the submission, describe this mapping instead of introducing new schemas.

| Plan concept | Repository realization | Notes |
|---|---|---|
| IntentSpec | `intent` section of HarnessSpec v0.2 | Goal, scope, exclusions. |
| DomainSpec | `sources`, domain skills (`SKILL.md`), report template, case data | No dedicated schema; domain knowledge is carried as referenced assets with authority/provenance. |
| Methodology | `methodology` section + `methodology.yaml` (ATAM) + `stages` readiness/completion criteria | Methodology file holds detailed activities and evidence rules. |
| Methodology/semantic state | `semantic_state` in spec; `evaluation_results.semantic_state` in report contract | Kept separate from the runtime sidecar (`*.runtime.json`). |
| HarnessSpec / IR | `specs/harnessspec/v0.2.schema.json`, `src/harnessweaver/spec.py` | Spec is a design record, not an executable workflow. |
| Runtime adapter/materializer | Target references inside the `harness` skill (`src/harnessweaver/skills/harness/references/targets/`), applied by a coding agent; ATAM bundles exist, and the SARA target is pending generation | See [APPROACH.md](APPROACH.md) §3–4 and work items W3–W7. |
| Orchestration primitives | Generated path: Claude target uses what the skill selects at gate G2; DeepAgents target is a sequential stage pipeline. Hand-written reference: three `workflow_strategy × agent_interaction` pairs (supervisor, sequential pipeline, fan-out/fan-in) | Plan's *Loop* primitive is not implemented; report it as future work. |
| Checker / verifier / evaluator | Checker: `benchmarks/atam/pilot.py check` (deterministic). Evaluator: legacy ArchEval LLM judge (supplementary). Human review: protocol only. | No verifier with evidence trail beyond the checker. |

## 2. Inventory against the plan's "Must" items

| Plan item | Status | Evidence / location | What is missing |
|---|---|---|---|
| Freeze pilot method and example (ATAM banking) | **Done** | `pilots/atam/methodology.yaml`, `report-template.json`, `case-studies/architecture-eval/ATAM/data/banking.json` (inputs only) | — |
| Minimal versioned schemas + diagnostics | **Done** | `specs/harnessspec/v0.{1,2}.schema.json`, `hw validate`, `tests/test_spec.py` | — |
| Methodology state separate from runtime state | **Done** | `semantic_state` contract; `.runtime.json` sidecar; `tests/test_atam_demo.py` | — |
| Generator shared assets → HarnessSpec | **Partial** | Authored sources in `pilots/atam/sources/` (W2); design phase of the `harness` skill (gates G0–G3) not yet run. The existing ATAM HarnessSpec v0.2 is hand-authored | W5 (generation session). If time runs short, keep the hand-written spec and say so. |
| Claude materializer | **Partial** | Claude Code target reference in the `harness` skill; never run. `pilots/atam/claude-plugin/` is a hand-written reference realization | W5 (generation), W6 (execution) |
| DeepAgents adapter | **Partial** | Execution adapter + 3 profiles, fake-agent tests; provider runs in `benchmarks/atam/pilot-status.md` | The generated path (stage directories + `wiring.yaml`) runs on the stage host (W4, tested offline through real DeepAgents middleware) once a generation session (W5) produces it. The hand-written runner is a reference realization; under the current semantic-state contract only its **supervisor** profile has a passing provider run. |
| Checks/evaluators | **Done** (checks) / **Partial** (review) | `hw check-bundle`; `hw check` (schema, `atam-pilot` via `pilot.py check`, reference leakage); blind review protocol defined, no reviews done | Human review is out of scope for the submission; state it. |
| Reproducible packaging | **Partial** | `docs/quickstart.md`, `pilots/atam/deepagents/README.md` | Run records under `benchmarks/*/runs/` and `pilots/atam/deepagents/runs/` are **git-ignored**, so the evidence package is not versioned (W8). No anonymized artifact (W10). |

Stretch items:

| Plan item | Status | Evidence / location |
|---|---|---|
| Named orchestration patterns | **Done** for three patterns | `src/harnessweaver/runtime/`, `tests/test_runtime.py`, `tests/test_deepagents_runtime.py` |
| Second domain (design) | **Partial** | SARA's 4-stage/11-skill source packet and CampusBike case are prepared in `pilots/sara/`; generation, bundle check and run remain pending. |
| Evolution workflow | **Partial** | Evidence-linked prompt revision (sequential scenario-ID fix) and semantic-state contract refresh, both recorded in `pilot-status.md`. No "edit sources or spec → regenerate" demo yet (W11). |

Other existing work not in the plan:

- **SAAM WRCS pilot** (`pilots/saam/`, `benchmarks/saam/`): matched baseline vs spec-guided runs, DeepAgents/Pydantic only, partial reference (6/15 scenarios). Not a two-runtime case.
- **Portable-skill preparation** (`benchmarks/atam/runs/u7-portability-skill-20261020/`): input preparation and mapping by a non-Claude coding agent; no execution.
- **Generation skills** (`src/harnessweaver/skills/harness`, `evolve`; `deepagents-port` merged into `harness` on 2026-10-24): LLM-driven design and generation method. Derived from `revfactory/harness`; the paper must disclose this lineage.

## 3. Pilots for the submission

| Pilot | Role in paper | Domain / method | Runtimes | Decision |
|---|---|---|---|---|
| **P1 · ArchEval-ATAM (banking)** | Minimum matrix, RQ1–RQ2; generation-baseline comparison (Claude) | Architecture evaluation / ATAM | Claude Code project + DeepAgents stage pipeline, both generated | **Committed.** Method, case, checker and reference realizations exist; sources layout and both generated targets are missing. |
| **P2 · SARA (design)** | RQ3 (domain flexibility); also the concrete example of the *bespoke application* strategy in Figure 1 | Architecture design: requirements → drivers → patterns/alternatives → evaluation → ADR | DeepAgents backend generated for the standalone HarnessWeaver stage host; SARA application integration is stretch | **Prepared for generation.** CampusBike selected; host and JSON-output adaptations are documented in `pilots/sara/`. |
| SAAM WRCS | One sentence as ongoing work | Architecture evaluation / SAAM | DeepAgents only | Parked. |
| ADD design exploration | Future work | Architecture design / ADD | None | Parked; superseded by SARA for this submission. |
| ATAM portable-skill case (`G1-anonymized-blind-eng.pdf` input) | Not used | ATAM | — | Parked. |

Why SARA rather than the ADD profile: SARA already encodes a design methodology as 4 stage `AGENTS.md` files and 11 `SKILL.md` files (~1.3k lines), coupled to Firebase/Firestore and Gemini in application code (`factory.py`, `stages.py`, `pipeline_service.py`). Harvesting it into authored sources, designing a HarnessSpec, and regenerating the DeepAgents stage directories tests domain flexibility with real, independently written material. The DeepAgents target pattern was itself distilled from SARA, so the comparison with SARA's originals also measures skill fidelity. The ADD profile has neither a case nor runnable assets.

The resulting matrix is therefore asymmetric: P1 shows **runtime flexibility** (one method, two runtimes) and P2 shows **domain flexibility** (a second method, one runtime, embedded in an existing application). State this explicitly in the validation matrix rather than presenting a full 2 × 2.

### 3.1 P2 scope and conditions

1. **Generated part:** the DeepAgents backend only (stage agents, skills, artifact contracts, sequential orchestration), materialized from a SARA HarnessSpec v0.2. SARA's existing stage `AGENTS.md`/`SKILL.md` files are the domain/methodology source.
2. **Selected host:** the first run uses the generic HarnessWeaver stage host, filesystem hand-offs and its JSON artifact validation. It is a standalone workflow-transfer exercise; it does not establish compatibility with SARA's frontend, API, Firestore, auth, or `PipelineService`.
3. **Output adaptation:** SARA's source workflow emits `adr.md` and `architecture_diagram.mmd`; the HarnessWeaver host accepts JSON artifacts. Package their text as `adr_markdown` and `architecture_diagram_mermaid` in a schema-validated `architecture_decision.json`. Report this format change explicitly.
4. **Known source defects:** SARA's Stage 1 call-contract mismatch does not block the standalone run but remains a blocker for SARA-host integration. The Stage 4 diagram skill refers to `/adr.json` while the ADR skill emits `/adr.md`; preserve and report the source mismatch, then use a consistent HarnessWeaver-side hand-off.
5. **Input case:** CampusBike, the ReArch paper case. The binding uses only the system description and 13 functional requirements; prior outputs, workflow state and vector databases are excluded.
6. **SARA integration:** adapting SARA's frontend/API is stretch work, only after ownership and the Stage 1 contract are resolved in the case-study repository (`NicolasMP51/software-architecture-agent`, revision `528ae7c`, nested and not tracked here).

## 4. Remaining work (ordered)

The approach is defined in [APPROACH.md](APPROACH.md). Work items are numbered W1–W12 (gates of the `harness` skill are G0–G6). **Owner:** *dev* = development agent; *user* = runs Claude Code sessions with skills and returns the records (APPROACH §9.8).

| ID | Work | Pilot | Owner | Priority | Completion criterion |
|---|---|---|---|---|---|
| W1 | ~~Unified `harness` + `evolve` skills~~ in `src/harnessweaver/skills/` | All | dev | Done 2026-10-24 | Gates G0–G6, answers file, both target references, materialization report template |
| W2 | ~~ATAM `sources/` layout (`intent.yaml`, `methodology.yaml`, `domain/` with skills and JSON Schema of the report); `cases/banking.yaml`~~ | P1 | dev | Done 2026-10-25 | Sources contain no runtime constructs or case data; schema matches the Pydantic report model. (The current hand-written spec still cites `banking.json` as stage inputs; generated specs must use artifact ids.) |
| W3 | ~~`hw sandbox create-generation/create-execution/collect/record`, `RUNBOOK.md` and `run.sh` templates, `hw check-bundle` for both targets, `hw check` (schema, `atam-pilot`, reference leakage)~~ | All | dev | Done 2026-10-25 | Tests cover input-only extraction, no evaluator-only data in sandboxes, bundle checks |
| W4 | ~~HarnessWeaver DeepAgents stage host reading `wiring.yaml`~~ (`src/harnessweaver/hosts/deepagents.py`) | P1, P2 | dev | Done 2026-10-25 | Fake-agent tests for stage order, artifact checks and schema validation |
| W5 | P1 generation sandbox: `harness` session producing spec, Claude form and DeepAgents form | P1 | user (dev prepares) | Must | Generated files collected into `pilots/atam/`; generation record; bundle checks pass or failures listed |
| W5b | P1 baseline arm: revfactory/harness v2.1.0 skills in English (`baselines/revfactory-harness-v2.1.0-en/`) in a generation sandbox with the same sources and prompt → Claude project → execution run | P1 | user (dev prepares, analyzes) | Must | Both arms scored with the same coverage checklist and ATAM checker (`BASELINE.md`) |
| W6 | P1 execution runs: Claude form (user) and DeepAgents form on the stage host (dev, `openai:gpt-5.4-mini`) on banking | P1 | user + dev | Must | Outputs checked with the ATAM checker; records in the evidence package |
| W7 | P2 harvest + design + DeepAgents form (user session), standalone stage-host run (dev) | P2 | user + dev | Must | Harvest report; spec validates; stage dirs compared with SARA's originals; run recorded |
| W8 | Curated evidence package in `docs/cain-2027/evidence/` | All | dev | Must | Every record cited in the paper is versioned |
| W9 | Effort and intervention log (`docs/cain-2027/effort-log.md`) | All | dev + user | Must | Consistent fields; retrospective entries labelled |
| W10 | Anonymized artifact | All | dev | Must | No author names, third-party PDFs or nested repos |
| W11 | P2b SARA methodology variation → regenerate → run | P2 | user + dev | Stretch | Diff sources → spec → bundle, files changed, run outcome |
| W12 | Connect SARA's API/frontend to the generated backend | P2 | dev | Stretch | Integration changes logged in `pilots/sara/integration.md` |

Not planned for the submission: the Loop primitive, separate Intent/Domain schemas, SAAM on a second runtime, human blind review, generating the U7 supervisor/fan-out profiles.

## 5. Decisions (2026-10-24)

- **Pilots:** P1 ArchEval-ATAM (Claude + DeepAgents); P2 SARA (generated DeepAgents backend, SARA app adapted), with an optional P2b methodology variation. SAAM and ADD are parked.
- **P1 DeepAgents model:** `openai:gpt-5.4-mini`, reusing existing evidence; the model mismatch with the Claude cell is a declared limitation.
- **Language:** everything runs in English: skills, prompts, gate answers, generated artifacts.
- **Generation baseline:** revfactory/harness v2.1.0 skills in a direct English translation (`baselines/revfactory-harness-v2.1.0-en/`), Claude runtime only (W5b).
- **Approach:** see [APPROACH.md](APPROACH.md) §9 (skill-driven generation, Claude project target, DeepAgents stage pattern with a HarnessWeaver host, committed generated files, `benchmarks/` kept for now, directory sandboxes, user-run Claude sessions).

## 6. Repository reorganization (applied 2026-10-24)

- `examples/` → `pilots/` (`atam`, `saam`, `design-exploration`, new `sara`). Python imports changed from `examples.atam…` to `pilots.atam…`; spec-relative paths are unchanged because the depth is the same. Index: [`pilots/README.md`](../../pilots/README.md).
- `docs/cain-2027/`: this file, [APPROACH.md](APPROACH.md) and the co-author plan (moved from the root). The effort log and evidence package go here (W8, W9).
- [`docs/README.md`](../README.md): classifies docs as current, pilot-specific, reference, or historical. Files were not moved because the harness-skill docs cross-reference each other and the skills.
- `harness-en/` → `src/harnessweaver/skills/` (two skills, `harness` and `evolve`).
- Upstream-derived docs (`*_EN.md`, the Korean migration guide) → `legacy/revfactory-harness/`.
- `baselines/revfactory-harness-v2.1.0/` (verbatim upstream skills, Korean) and `baselines/revfactory-harness-v2.1.0-en/` (direct English translation used in runs).
- `benchmarks/` and `case-studies/`: unchanged. Git-ignored historical run records (`benchmarks/atam/runs/`, `pilots/atam/deepagents/runs/`) still cite `examples/…` paths; they are kept as recorded.
