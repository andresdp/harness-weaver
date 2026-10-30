# Materialization Report — SARA → Claude Code harness

Generated 2026-10-29 with the RevFactory Harness v2 baseline (English arm). Target: Claude Code agents, skills,
orchestrator skill and `CLAUDE.md` only.

## 1. Sources used

| Source | Role | How it was used |
|--------|------|-----------------|
| 4 × stage `AGENTS.md` (SARA @ `528ae7c`) | Workflow authority: stage order, task order, rules, completion protocol | One agent per stage (`.claude/agents/sara-*.md`) |
| 11 × task `SKILL.md` | Task procedures and artifact shapes | One project skill per task, same name, with procedures and rules preserved and paths normalized |
| `domain/contracts/architecture-decision.schema.json` | Required final output shape | Copied byte-for-byte to `sara-artifact-review/references/`; inlined as the packaging step's `schema` in the workflow |
| `host-adaptation.md` | Context only (output boundary) | Used for: input port names, JSON envelope with ADR/Mermaid as strings, no new mid-run human gate, the `/adr.json` defect. No HarnessWeaver host, HarnessSpec, wiring or adapter was implemented. |

No case material was read or used. The harness contains no case-specific content.

## 2. Coverage

| SARA element | Generated as | Status |
|--------------|--------------|--------|
| Stage 1 orchestrator | `sara-requirements-analyst` agent | Covered |
| requirements-cross-analysis, quality-attribute-identification, driver-identification | Skills of the same names | Covered |
| Stage 2 orchestrator | `sara-solution-designer` agent | Covered |
| pattern-candidate-identification, patterns-compatibility, alternative-generation | Skills of the same names | Covered |
| Stage 3 orchestrator | `sara-alternative-evaluator` agent | Covered |
| alternative-evaluation, trade-off-analysis, alternative-selection | Skills of the same names | Covered |
| Stage 4 orchestrator | `sara-decision-documenter` agent | Covered (with corrections, §4) |
| adr-generation, architecture-diagram | Skills of the same names | Covered (with corrections, §4) |
| Fixed stage order 1→2→3→4 | `Workflow` script in `sara-orchestrator` (sequential fallback via `Agent`) | Covered |
| Ordered tasks within a stage, one at a time | Agent instructions | Approximated: the agent follows the order; nothing enforces it at runtime |
| "Read SKILL.md before each task" | Agent instructions + `skills:` preload | Covered |
| Write → read back → verify JSON after each task | Agent self-check + reviewer after each stage | Approximated: no deterministic JSON or JSON Schema validation (§5) |
| Mandatory completion protocol | Agent instructions, `STAGE_STATUS` return, reviewer existence check, workflow halts on `fail` | Covered at stage granularity |
| Stage boundary rules (e.g. no solutions in Stage 1) | Skill rules + reviewer checklist | Approximated: judged by the model |
| Traceability decision → requirements/QAs/drivers | ADR Traceability section; exact-ID/name rules; reviewer cross-reference checks | Covered (model-checked) |
| Final JSON contract | `sara-decision-packager` + workflow `schema: DECISION` + package review | Covered, with the caveat in §5 |
| Assumptions and unresolved gaps | `assumptions-gap-register` skill, per-stage registers, ADR section, `output/assumptions_and_gaps.json` | Added by the harness (§3) |

## 3. Harness additions (not in SARA)

1. **Gap register** (`stage{N}_assumptions_gaps.json`, merged into `output/assumptions_and_gaps.json`). The request
   requires assumptions and gaps to be recorded, and the contract allows no extra properties, so they go in a
   sidecar file. The register only collects items. It follows SARA's rule against resolving ambiguities by invention.
2. **ADR section "Assumptions and Unresolved Gaps"**, added after Traceability. This puts the gaps inside
   `adr_markdown` in the contract file. It is the only change to the SARA ADR template.
3. **Contract reviewer after every stage**, with one bounded repair loop. The review is read-only. Fixes come from
   the agent that owns the artifact, so the stage content keeps a single author. SARA's own self-verification is
   still in place.
4. **Packaging step**: copies the reviewed content verbatim into the contract envelope.
5. **Small enumerations** (`relationship_type`, `relationship`, `impact`, priority). They narrow free-text values the
   source leaves open, so cross-artifact checks are possible. They are marked as harness additions in the schemas.
6. **Requirement ID labeling** (`RF1..n`) when the input has no IDs. It is recorded as a `process_note`.

## 4. Source defects found and how they were handled

| Defect in source | Handling |
|------------------|----------|
| The Stage 4 diagram skill reads `/adr.json`, but the ADR skill writes `/adr.md` | The harness uses `_workspace/artifacts/adr.md` as the handoff. Noted in the skill and the agent |
| `patterns-compatibility` reads `/artifacts/drivers.json`; all other skills use `/drivers.json` | All artifacts live under `_workspace/artifacts/` |
| Every stage's rules say "write its artifact to /artifacts/", while outputs are declared at `/` | Normalized to `_workspace/artifacts/` |
| The Stage 4 protocol says "Before ending the **Stage 3** workflow" and "all **three** artifacts" but lists two files | Treated as Stage 4. The third file is the stage gap register |
| The Stage 4 rules ask for "valid JSON" for `.md`/`.mmd` outputs | Replaced with well-formed Markdown and Mermaid checks |
| Stage 4 inputs omit the Stage 1 artifacts, but the ADR procedure needs requirements and drivers for traceability | Stage 4 also gets read-only access to the Stage 1 artifacts and `alternatives.json` |

## 5. Limitations, unsupported and approximated requirements

- **No deterministic validation.** The scope rules out project-specific validator code. JSON validity is checked by
  read-back, plus `python3 -m json.tool` or `jq` if they are installed. JSON Schema conformance is checked by the
  model reading the declarative schemas, unless an off-the-shelf CLI is present. Mermaid and Markdown validity is
  checked structurally, not by rendering. These checks are **approximated**.
- **Final contract enforcement.** In workflow mode, the packager's return value is validated against an inline copy
  of the contract through `agent(..., {schema})`. It is not established here whether `pattern` and `minLength` are
  enforced by that mechanism. The file on disk is checked by the reviewer and the main agent. In fallback mode
  there is no schema-checked return.
- **Ordering inside a stage** depends on the agent following its instructions. Nothing at runtime blocks a task
  from reading an artifact before it exists.
- **`Workflow` tool availability.** The `Workflow` tool was not available in the generation session, so the script
  was only checked for syntax. It has not been executed. The fallback path is documented but also untested.
- **No end-to-end run.** No case was supplied at generation time, and the scope requires independence from the
  case, so no execution tests or with/without-skill comparison were run. Verification was static only (§6).
- **Partial re-runs** lose earlier stages' non-blocking review findings from the carried list, unless the main
  agent merges the previous `_workspace/review_findings.json`. The gap registers themselves are kept.
- **Fidelity boundary.** This is a standalone materialization of the SARA workflow in Claude Code. It does not show
  drop-in compatibility with the SARA application (Firestore, UI, `PipelineService`) or behavioral equivalence to it.
- **Model choice.** Stages 1–3 use opus. Stage 4, the review and packaging use sonnet. These are design judgments
  and have not been benchmarked.

## 6. Verification performed

- All 6 agents and 15 skills have `name` and `description` in their frontmatter, and each skill directory name
  matches its `name`.
- Every `agentType`, every `skills:` entry and every `.claude/skills/...` path resolves.
- Both reference schemas parse. The contract copy is byte-identical to the source.
- The workflow script passes `node --check`. Its `meta` holds only literals, it does not use
  `Date.now`/`Math.random`/`new Date`, its phase titles match `meta.phases`, and it handles `null` results
  explicitly. It has no `parallel()`, because the stages are strictly sequential.
- There are no `.claude/commands/`, no v1 team constructs, no executable scripts and no case-specific content.

## 7. File inventory

```
CLAUDE.md  README.md  MATERIALIZATION_REPORT.md
.claude/agents/   sara-requirements-analyst, sara-solution-designer, sara-alternative-evaluator,
                  sara-decision-documenter, sara-contract-reviewer, sara-decision-packager
.claude/skills/   sara-orchestrator; 11 SARA task skills; assumptions-gap-register;
                  sara-artifact-review (+ references/architecture-decision.schema.json,
                  references/sara-stage-artifacts.schema.json); architecture-decision-packaging
```
