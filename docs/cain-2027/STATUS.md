# CAIN 2027: implementation status, pilots, and gaps

**Reviewed:** 2026-10-24 (branch `feat/harnessweaver-u4-u7`, 75 unit tests passing).
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
| Runtime adapter/materializer | DeepAgents adapter (`src/harnessweaver/adapters/deepagents/`) executes; **no materializer emits files for either runtime** | See gaps G1–G2. |
| Orchestration primitives | Three `workflow_strategy × agent_interaction` pairs (supervisor, sequential pipeline, fan-out/fan-in) | Plan's *Loop* primitive is not implemented; report it as future work. |
| Checker / verifier / evaluator | Checker: `benchmarks/atam/pilot.py check` (deterministic). Evaluator: legacy ArchEval LLM judge (supplementary). Human review: protocol only. | No verifier with evidence trail beyond the checker. |

## 2. Inventory against the plan's "Must" items

| Plan item | Status | Evidence / location | What is missing |
|---|---|---|---|
| Freeze pilot method and example (ATAM banking) | **Done** | `pilots/atam/methodology.yaml`, `report-template.json`, `case-studies/architecture-eval/ATAM/data/banking.json` (inputs only) | — |
| Minimal versioned schemas + diagnostics | **Done** | `specs/harnessspec/v0.{1,2}.schema.json`, `hw validate`, `tests/test_spec.py` | — |
| Methodology state separate from runtime state | **Done** | `semantic_state` contract; `.runtime.json` sidecar; `tests/test_atam_demo.py` | — |
| Generator shared assets → HarnessSpec | **Missing** (by design) | HarnessSpec v0.2 is hand-authored | Decide: keep spec hand-authored and describe it as the authored source (recommended), not as generated output. |
| Claude materializer | **Missing** | `pilots/atam/claude-plugin/` is hand-maintained; skill-driven generation procedure exists in `pilots/atam/CLAUDE-TESTING.md` §B but was never run | G1 |
| DeepAgents adapter | **Partial** | Execution adapter + 3 profiles, fake-agent tests; provider runs in `benchmarks/atam/pilot-status.md` | Assets (`agents.yaml`, skills, prompts) are hand-maintained, not emitted from the spec (G2). Under the current semantic-state contract only **supervisor** has a passing provider run. |
| Checks/evaluators | **Done** (checker) / **Partial** (review) | `pilot.py check`; blind review protocol defined, no reviews done | Human review is out of scope for the submission; state it. |
| Reproducible packaging | **Partial** | `docs/quickstart.md`, `pilots/atam/deepagents/README.md` | Run records under `benchmarks/*/runs/` and `pilots/atam/deepagents/runs/` are **git-ignored**, so the evidence package is not versioned (G5). No anonymized artifact (G6). |

Stretch items:

| Plan item | Status | Evidence / location |
|---|---|---|
| Named orchestration patterns | **Done** for three patterns | `src/harnessweaver/runtime/`, `tests/test_runtime.py`, `tests/test_deepagents_runtime.py` |
| Second domain (design) | **Missing** | ADD profile in `pilots/design-exploration/` has no case and no run; SARA mapping is read-only (`docs/software-architecture-agent-mapping.md`) |
| Evolution workflow | **Partial** | Evidence-linked prompt revision (sequential scenario-ID fix) and semantic-state contract refresh, both recorded in `pilot-status.md`. No "edit spec → regenerate both targets" demo (depends on G1–G2). |

Other existing work not in the plan:

- **SAAM WRCS pilot** (`pilots/saam/`, `benchmarks/saam/`): matched baseline vs spec-guided runs, DeepAgents/Pydantic only, partial reference (6/15 scenarios). Not a two-runtime case.
- **Portable-skill preparation** (`benchmarks/atam/runs/u7-portability-skill-20261020/`): input preparation and mapping by a non-Claude coding agent; no execution.
- **Harness design skills** (`harness-en/skills/harness`, `evolve`, `deepagents-port`): LLM-driven design/generation method. Derived from `revfactory/harness`; the paper must disclose this lineage.

## 3. Pilots for the submission

| Pilot | Role in paper | Domain / method | Runtimes | Decision |
|---|---|---|---|---|
| **P1 · ArchEval-ATAM (banking)** | Minimum matrix, RQ1–RQ2 | Architecture evaluation / ATAM | Claude plugin + DeepAgents | **Committed.** Most assets exist; only the Claude cell and materialization are missing. |
| **P2 · SARA (design)** | RQ3 (domain flexibility); also the concrete example of the *bespoke application* strategy in Figure 1 | Architecture design: requirements → drivers → patterns/alternatives → evaluation → ADR | DeepAgents backend only, generated or approximated by HarnessWeaver; SARA's frontend/API adapted to connect to it | **Committed** (decided 2026-10-24). |
| SAAM WRCS | One sentence as ongoing work | Architecture evaluation / SAAM | DeepAgents only | Parked. |
| ADD design exploration | Future work | Architecture design / ADD | None | Parked; superseded by SARA for this submission. |
| ATAM G1 portable-skill | Not used | ATAM | — | Parked. |

Why SARA rather than the ADD profile: SARA already encodes a design methodology as 4 stage `AGENTS.md` files and 11 `SKILL.md` files (~1.3k lines), coupled to Firebase/Firestore and Gemini in application code (`factory.py`, `stages.py`, `pipeline_service.py`). Re-expressing it as HarnessSpec v0.2 with `sequential_pipeline + typed_artifact_handoffs` (an already supported profile) and reusing its skills as domain assets tests domain flexibility with real, independently written material. The ADD profile has neither a case nor runnable assets.

The resulting matrix is therefore asymmetric: P1 shows **runtime flexibility** (one method, two runtimes) and P2 shows **domain flexibility** (a second method, one runtime, embedded in an existing application). State this explicitly in the validation matrix rather than presenting a full 2 × 2.

### 3.1 P2 scope and conditions

1. **Generated part:** the DeepAgents backend only (stage agents, skills, artifact contracts, sequential orchestration), materialized from a SARA HarnessSpec v0.2. SARA's existing stage `AGENTS.md`/`SKILL.md` files are the domain/methodology source.
2. **Adapted part:** SARA's frontend and API (`PipelineService`, Firestore backend, auth) are connected to the generated backend. Record each required change, whether it is in SARA or in HarnessWeaver output, and its effort. Changes to SARA code belong to its repository (`NicolasMP51/software-architecture-agent`, revision `528ae7c`, nested and not tracked here).
3. **Known blocker:** SARA's Stage 1 call-contract mismatch (`get_stage_message` vs `build_stage1_message`) must be resolved on SARA's side or bypassed by the generated backend's entry point; record which.
4. **Input case:** one project description + functional requirements, ideally a case SARA has already processed so outputs can be compared by inspection.
5. **Time box:** if the generated backend is not running inside SARA by 28 Oct, report "spec + generated backend, standalone run" and list the integration as future work.

## 4. Remaining work (ordered)

| ID | Work | Pilot | Priority | Completion criterion |
|---|---|---|---|---|
| G1 | `hw materialize --target claude`: emit plugin (`plugin.json`, `agents/*.md` from `roles`, skills and shared references copied from one source) + `materialization-manifest.json` (concept → construct, unsupported/lossy list) | P1 | Must | Generated plugin passes `claude plugin validate`; diff against the hand-maintained plugin recorded as intervention log. |
| G2 | `hw materialize --target deepagents`: emit `agents.yaml`, skills, references, manifest consumed by the existing runner | P1 | Must | Existing runner executes from generated assets; tests cover generation determinism. |
| G3 | Live Claude run of the generated plugin on banking (inputs only) + `pilot.py check` | P1 | Must | Report file + check output + Claude Code/model versions recorded. |
| G4 | DeepAgents supervisor run from generated assets (same case, `openai:gpt-5.4-mini`) | P1 | Must | Passing check under current contract. The model differs from the Claude cell; report it as a limitation. |
| G5 | Version a curated evidence package (selected run records, manifests, checker outputs) outside ignored paths | P1 | Must | `docs/cain-2027/evidence/` (or equivalent) contains every record cited in the paper. |
| G6 | Anonymized artifact (no author names, no third-party PDFs, no nested repos) | All | Must | Anonymous link builds and reproduces generation. |
| G7 | Effort/intervention log started now; retrospective entries from git history labelled as such | All | Must | `docs/cain-2027/effort-log.md` with consistent fields. |
| G8 | Evolution demo: one spec change → regenerate both targets → count changed files | P1 | Stretch | Before/after manifests and diff stats. |
| G9 | SARA HarnessSpec v0.2 + `methodology.yaml` derived from its stage files | P2 | Must | Spec validates; every stage/task/artifact traces to a SARA source file. |
| G9a | Generate the SARA DeepAgents backend (reuses G2) + standalone run on one input case | P2 | Must | Four stages produce their declared artifacts; run record kept. |
| G9b | Connect SARA's API/frontend to the generated backend | P2 | Stretch | End-to-end run through SARA's UI or API; integration changes and effort logged in `pilots/sara/integration.md`. |
| G10 | Bounded retries of sequential/fan-out under current contract | P1 | Optional | One attempt each with a hard timeout; record outcome either way. |

Not planned for the submission: Loop primitive, separate Intent/Domain schemas, LLM-based spec generation, SAAM second runtime, human blind review.

## 5. Decisions (2026-10-24)

- **Pilots:** P1 ArchEval-ATAM (Claude + DeepAgents); P2 SARA (generated DeepAgents backend, SARA app adapted). SAAM and ADD parked.
- **P1 DeepAgents model:** `openai:gpt-5.4-mini`, reusing existing evidence; model mismatch with the Claude cell is a declared limitation.
- **Reorganization:** medium (see §6).

## 6. Repository reorganization (applied 2026-10-24)

- `examples/` → `pilots/` (`atam`, `saam`, `design-exploration`, new `sara`). Python imports changed from `examples.atam…` to `pilots.atam…`; spec-relative paths are unchanged because the depth is the same. Index: [`pilots/README.md`](../../pilots/README.md).
- `docs/cain-2027/`: this file and the co-author plan (moved from the root). The effort log and evidence package go here (G5, G7).
- [`docs/README.md`](../README.md): classifies docs as current, pilot-specific, reference, or historical. Files were not moved because the harness-skill docs cross-reference each other and `harness-en/`.
- `benchmarks/` and `case-studies/`: unchanged. Git-ignored historical run records (`benchmarks/atam/runs/`, `pilots/atam/deepagents/runs/`) still cite `examples/…` paths; they are kept as recorded.
