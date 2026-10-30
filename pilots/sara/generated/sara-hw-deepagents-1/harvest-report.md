# Harvest report: SARA architecture-design workflow

- Upstream: `NicolasMP51/software-architecture-agent@528ae7ce0b054ee1631bd091fe6b759208bbbb6c`
- Input packet: `sources/harvest-input/` (4 `AGENTS.md`, 11 `SKILL.md`); left unmodified.
- Design inputs used: the packet, `sources/host-adaptation.md`, `sources/domain/contracts/architecture-decision.schema.json`, `sources/domain/sources.yaml`.
- Not used: any execution case, case examples or reference outputs. No case facts appear in the drafts.
- Date: 2026-10-29. Harvested by the HarnessWeaver `harness` skill (Claude Code, Claude Opus 5.5).

## 1. Inventory

| Item | Origin (under `backend/app/agents/`) | Kind | Draft location | Handling |
|---|---|---|---|---|
| Stage 1 orchestrator | `stage1-requirements_drivers/AGENTS.md` | stage instructions | `sources/domain/stage-instructions/stage1-requirements_drivers.AGENTS.md` | copied verbatim; summarized in `methodology.yaml` |
| Stage 2 orchestrator | `stage2-solution_design/AGENTS.md` | stage instructions | `…/stage2-solution_design.AGENTS.md` | copied verbatim; summarized |
| Stage 3 orchestrator | `stage3-alternative_evaluation/AGENTS.md` | stage instructions | `…/stage3-alternative_evaluation.AGENTS.md` | copied verbatim; summarized |
| Stage 4 orchestrator | `stage4-architecture_decision/AGENTS.md` | stage instructions | `…/stage4-architecture_decision.AGENTS.md` | copied verbatim; summarized |
| requirements-cross-analysis | stage1 `skills/…/SKILL.md` | domain skill | `sources/domain/skills/requirements-cross-analysis/SKILL.md` | copied verbatim |
| quality-attribute-identification | stage1 | domain skill | `sources/domain/skills/…` | copied verbatim |
| driver-identification | stage1 | domain skill | `sources/domain/skills/…` | copied verbatim |
| pattern-candidate-identification | stage2 | domain skill | `sources/domain/skills/…` | copied verbatim |
| patterns-compatibility | stage2 | domain skill | `sources/domain/skills/…` | copied verbatim |
| alternative-generation | stage2 | domain skill | `sources/domain/skills/…` | copied verbatim |
| alternative-evaluation | stage3 | domain skill | `sources/domain/skills/…` | copied verbatim |
| trade-off-analysis | stage3 | domain skill | `sources/domain/skills/…` | copied verbatim |
| alternative-selection | stage3 | domain skill | `sources/domain/skills/…` | copied verbatim |
| adr-generation | stage4 | domain skill | `sources/domain/skills/…` | copied verbatim |
| architecture-diagram | stage4 | domain skill | `sources/domain/skills/…` | copied verbatim |
| Final output envelope | `sources/domain/contracts/architecture-decision.schema.json` | pilot contract (not SARA) | `sources/domain/contracts/` | copied verbatim |

All 16 copies were hash-checked against `sources/harvest-input/PROVENANCE.md`; every SHA-256 matches.

### Declared artifact contracts (from the skills' JSON structure blocks)

| Stage | Task | SARA artifact | Top-level shape | Cross-references |
|---|---|---|---|---|
| 1 | requirements-cross-analysis | `/requirements_analysis.json` | `requirements[]`, `cross_requirement_relationships[]` | `requirement_id` (e.g. `RF1`) |
| 1 | quality-attribute-identification | `/quality_attributes.json` | `quality_attributes[]` | `source_requirement_ids` |
| 1 | driver-identification | `/drivers.json` | `drivers[]` | `source_requirement_ids` |
| 2 | pattern-candidate-identification | `/pattern_candidates.json` | `pattern_candidates[]` | `source_requirement_ids`, `source_driver_names` |
| 2 | patterns-compatibility | `/pattern_compatibility.json` | `compatibility_analysis[]` | `patterns` (names), `affected_drivers` |
| 2 | alternative-generation | `/alternatives.json` | `alternatives[]` | `alternative_id`, `selected_patterns`, `addressed_drivers` |
| 3 | alternative-evaluation | `/alternative_evaluation.json` | `evaluations[]` | `alternative_id`, `requirement_id`, driver, quality attribute |
| 3 | trade-off-analysis | `/trade_off_analysis.json` | `trade_offs[]` | `alternative_id` |
| 3 | alternative-selection | `/alternative_selection.json` | `selected_alternative_id`, `rejected_alternatives[]`, … | `alternative_id` |
| 4 | adr-generation | `/adr.md` | Markdown, `# ADR: <title>` + fixed sections | prose traceability |
| 4 | architecture-diagram | `/architecture_diagram.mmd` | Mermaid source, prefer `flowchart LR`, no fences | — |

## 2. Layer separation

| Layer | Content | Destination |
|---|---|---|
| Intent | Goal, users, decision supported, scope, exclusions | `sources/intent.yaml` (summarized; human-review need marked *inferred*) |
| Methodology | 4 serial stages, 11 serial tasks, read/write sets, execution discipline, completion protocols, evidence rules, scope boundaries | `sources/methodology.yaml` (summarized with `copied/summarized/inferred/adaptation` labels; semantic checkpoints *inferred*) |
| Domain knowledge | Task procedures, rules, Correct/Incorrect examples, JSON structure blocks | `sources/domain/skills/` (verbatim) and `sources/domain/sources.yaml` |
| Runtime bindings | SARA `PipelineService` stage loop, Firestore-backed project store and document checks, frontend, API routing, authentication, model factory | **Not harvested.** Listed below as host requirements of the original application only |

### Host requirements of the original SARA application (recorded, not targeted)

- A pipeline service that runs stages 1→4 serially, builds the Stage 1 hand-off message from project data, and checks stage artifacts after each run.
- A per-project artifact store at the virtual root (`/…json`) backed by Firestore; stage directories mounted as agent memory and skills.
- A model factory providing one chat model; user/project authentication; API and frontend.

None of these are inputs to the HarnessSpec. The pilot replaces them with the HarnessWeaver DeepAgents stage host (`sources/host-adaptation.md`).

## 3. Source defects (recorded, not fixed in the packet)

| ID | Defect | Where | Evidence | Effect | HarnessWeaver-side handling |
|---|---|---|---|---|---|
| **D1** | **Stage 1 call-contract mismatch.** SARA's Stage 1 message builder requires both `user_id` and `project_id`; its caller passes only `project_id`. | SARA application code (`PipelineService` path), **outside** the copied packet | `sources/host-adaptation.md` ("Why"); not observable in the 15 copied files | Stage 1 cannot be started through SARA's own host as written | Not reproduced: the pilot does not use `PipelineService`. The HarnessWeaver host writes the `project_description` and `functional_requirements` ports before Stage 1. Described in the materialization report. |
| **D2** | **Stage 4 ADR-path mismatch.** `adr-generation` writes `/adr.md`; `architecture-diagram` reads `/adr.json`; Stage 4 `AGENTS.md` expects `/adr.md`. | `stage4…/skills/architecture-diagram/SKILL.md` (Input Artifacts) vs `adr-generation/SKILL.md` and stage4 `AGENTS.md` | Direct reading of the files | The diagram task's declared input never exists; the ADR→diagram handoff is broken as written | Proposed: one consistent ADR handoff artifact written by ADR generation and read by the diagram task; reported as an adaptation. |
| D3 | Artifact location inconsistency: every `AGENTS.md` says "Write its artifact to /artifacts/", every skill writes to the root (`/requirements_analysis.json`), and `patterns-compatibility` reads `/artifacts/drivers.json` while its siblings read `/drivers.json`. | all stage `AGENTS.md`; `patterns-compatibility/SKILL.md` | Direct reading | An agent may look for a file in the wrong place | Proposed: use one location (`/artifacts/<name>.json`) in every generated stage and skill; reported as an adaptation of paths only. |
| D4 | Stage 4 completion protocol says "Before ending the **Stage 3** workflow" and "all **three** artifacts", but lists two files. | stage4 `AGENTS.md` | Direct reading | Copy-paste inconsistency; ambiguous completion count | Proposed: generated Stage 4 names itself and lists exactly its artifacts. |
| D5 | Stage 4 rules require reading back "valid JSON" although its outputs are Markdown and Mermaid; the diagram skill has no read-back sentence; ADR read-back is "valid Markdown" (no deterministic check). | stage4 `AGENTS.md`; `architecture-diagram/SKILL.md`; `adr-generation/SKILL.md` | Direct reading | Read-back checks are inconsistent or absent for Stage 4 | Resolved by the JSON envelope: Stage 4 artifacts become JSON with string fields, validated by schema (ADR must start `# ADR:`; diagram must start with a Mermaid diagram keyword). |
| D6 | Stage 4 input gap: the ADR procedure and rules require requirements, drivers and alternative names for context, rationale, "Alternatives Considered" and traceability, but Stage 4 and both Stage 4 skills only read `alternative_evaluation`, `trade_off_analysis`, `alternative_selection`. | stage4 `AGENTS.md`; `adr-generation/SKILL.md` (Procedure 2, 6, 7); `architecture-diagram/SKILL.md` ("project requirements") | Direct reading | ADR may lack alternative names/descriptions and requirement text; the agent may read undeclared files | **Open question (G1)**: keep SARA's declared inputs, or declare the Stage 1–2 artifacts as additional read-only Stage 4 inputs. |
| D7 | Weak cross-stage identifiers: quality attributes and drivers have no id fields; later artifacts reference them by name (`source_driver_names`, `affected_drivers`, `addressed_drivers`, `driver`). | stage1/2/3 skills' JSON blocks | Direct reading | Traceability relies on exact name matching | Preserved as-is (changing it would change artifact meaning); intermediate schemas do not add ids. Recorded for `evolve`. |
| D8 | Stage 1 input format is unspecified ("Project description", "Functional requirements"); only the `RF1` example implies an id convention. | stage1 `AGENTS.md`; `requirements-cross-analysis/SKILL.md` | Direct reading | Requirement ids depend on the caller | The ports are declared without imposing a format; the skill keeps the source's id example. |

## 4. Open questions for review

1. D6: should Stage 4 declare the Stage 1–2 artifacts it implicitly needs?
2. Semantic checkpoints in `methodology.yaml` are inferred (SARA tracks only file existence). Should they be checked post-run only, or emitted as an artifact by the harness?
3. The post-run architect review is inferred from the "recommendation" wording and `host-adaptation.md`; SARA has no explicit review gate.

The draft sources are ready for review before design begins.
