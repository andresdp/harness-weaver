# Materialization report: ATAM evaluation harness, Claude Code target

This report records how each source requirement was materialized in this bundle, and where the bundle departs from
or adds to the sources. Sources: `sources/intent.yaml`, `sources/methodology.yaml` and `sources/domain/*`.

## Target and scope

- **Target runtime:** Claude Code only. `intent.yaml` lists `[claude-code, deepagents]`, but the user chose to build
  only the Claude Code bundle for this generation, so no `deepagents` bundle was produced.
- **Input form:** template-shaped JSON (`ATAM_Evaluation.evaluation_inputs` plus optional `title` and `metadata`), as the user chose.
- **Language:** English.

## Verbatim copies (normative and unmodified)

| Source | Bundle location | Check |
| --- | --- | --- |
| `methodology.yaml` | `.claude/skills/evaluate-architecture/references/methodology.yaml` | byte-identical |
| `domain/contracts/atam-report.schema.json` | `.claude/skills/evaluate-architecture/references/atam-report.schema.json` | byte-identical; the stage 5 and 7 gates validate against it |
| `domain/contracts/analysis.schema.json` | `.claude/skills/evaluate-architecture/references/analysis.schema.json` | byte-identical; the stage 4 gate validates against it |
| `domain/references/atam-report-template.json` | `.claude/skills/evaluate-architecture/references/atam-report-template.json` | byte-identical |
| `domain/skills/{evaluate-architecture,check-evaluation,revise-report}/SKILL.md` | `.claude/skills/<same>/SKILL.md` | body verbatim; frontmatter `description` extended with invocation conditions; a `## Harness binding` section appended |

## Methodology activities → runtime stages

| Activity (methodology.yaml) | Stage | Agent / mechanism | Artifact |
| --- | --- | --- | --- |
| (input boundary) | `stage0-intake` | deterministic `atam.py intake` | `00_evaluation_inputs.json` |
| establish-context | `stage1-establish_context` | `atam-context-analyst` (sonnet) | `01_context.json` |
| build-utility-tree | `stage2-build_utility_tree` | `atam-utility-tree-builder` (opus) | `02_utility_tree.json` |
| identify-approaches | `stage3-identify_approaches` | `atam-approach-analyst` (opus) | `03_approaches.json` |
| analyze-scenarios | `stage4-analyze_scenarios` | `atam-scenario-analyst` (opus) | `04_analysis.json` |
| synthesize-and-review (synthesis) | `stage5-synthesize_report` | `atam-report-synthesizer` (sonnet) + `atam.py project-draft` | `05_atam_report_draft.json` only |
| synthesize-and-review (review) | `stage6-check_evaluation` | `atam-evaluation-checker` (opus) + `atam.py check` | `06_review_findings_initial.json` only |
| synthesize-and-review (revision and readiness) | `stage7-revise_report` | `atam-report-reviser` (opus) + `atam.py finalize` | `05_atam_report.json`, `06_review_findings.json` |

## How the user's specific requirements are enforced

| Requirement | Enforcement |
| --- | --- |
| Stages 5, 6 and 7 are three distinct, ordered runtime stages | `run.py` starts each stage as a separate `claude -p --agent` process. The `run_ledger.json` refuses `stage begin` unless every earlier stage completed and its output hashes are unchanged. In the fallback interactive mode the orchestrator makes one `Agent` call per stage against the same ledger. |
| Stage 5 writes only the draft; stage 6 only the initial findings; stage 7 only the two finals | Each `stage complete` diffs a pre-stage snapshot of the workspace and harness files and fails on any change outside the stage's `writes`. |
| Stage 6 reviews the draft and cannot report readiness | The `06_review_findings.schema.json` `initial` branch forbids `revision`, `ready_for_architect_review` and `readiness_basis`. The gate re-runs the automated checks and rejects missing or altered entries. |
| Stage 7 runs on every run, including when nothing needs correcting | The `run.py` loop has no skip condition. A run has no `06_review_findings.json` until stage 7 completes. Self-test `test_clean_run_still_executes_revision_stage` covers it. |
| Only stage 7 computes `ready_for_architect_review`; it stays false while any blocking fail or warn remains | `atam.py finalize` runs only while stage 7 is the started stage. It re-runs the automated checks on the final report, merges the reviser's reviewer checks, and sets readiness = (no warn or fail in any of the six blocking categories) AND (the ledger shows stages 0–6 completed in order before stage 7 began). The stage-7 gate recomputes it and rejects a hand-edited value. |
| Revision is evidence-preserving | The stage-7 gate rejects new finding, approach or scenario ids, changes to `evaluation_inputs`, dropped gaps, an evidence suffix that isn't a subset of the 04 ids, and an inferred→observed relabel. It also rejects a reviewer check marked `pass` when nothing changed at its location. |
| `analysis.schema.json` is used for the scenario-analysis artifact; `evidence_ids` stay in the allowed namespaces | The stage 4 gate validates against the verbatim contract and also checks that every cited id is registered (AE/BD in 01, AP in 03). |
| `G-*` ids appear only in gap records | The 01–04 gates scan every string outside `gaps`. The automated check `EVID-NO-GAP-IDS` scans the report outside `semantic_state.gaps` (and the input copy). The suffix regex accepts only `AE|AP|BD`. |
| Observed and inferred are distinguished in artifacts and reports | `basis` is recorded on every finding, approach, addressed attribute, measure and priority. The report carries it in the rationale suffix. `UNC-ABSENCE-BASIS` fails findings labelled observed whose wording rests on absence. |
| Absence is an inference about uncertainty | The same check, plus the skills' and agents' principles and the phrasing patterns in `references/artifacts.md`. |
| A qualitative performance proxy can't establish that a target is met or violated | Response measures exist only when observed in the inputs. Otherwise they are `null` plus a gap. `UNC-PERF-ATTAINMENT` warns on attainment wording in performance records that have no measure, and reviewer checks cover paraphrases. |
| Exact suffix `(evidence: AE-1, AE-2; basis: observed\|inferred)` on every risk and non-risk rationale | `project_report` appends it deterministically from the 04 fields. `EVID-RATIONALE-SUFFIX` (exact regex, exactly one occurrence) and `EVID-FINDING-TRACE` (ids and basis preserved) check it. |
| Reference boundary | Intake refuses any `ground_truth_outputs` key or unexpected top-level section. `REF-NO-REFERENCE-OUTPUTS` and `REF-INPUTS-PRESERVED` check the report. A settings deny rule covers `*ground_truth*` reads. |
| Human review | `report_status` is always `draft`, and `scenario_analysis_status` is never `reviewed` (forbidden by the analysis contract and checked). `readiness_basis.note` states that the draft must be reviewed by an architect before it informs a decision. |

## Additions (not in the sources)

- **Intermediate artifact schemas** for 01, 02, 03 and 06 (`atam_harness/schemas/`). The sources define only the
  report and the analysis contracts. These schemas give the AE/BD/AP registries and the review findings a
  checkable shape.
- **Run ledger, gates, projection, checks and finalize** (`atam_harness/atam.py`) and the stage runner
  (`atam_harness/run.py`).
- **Self-tests** (`atam_harness/tests/`) with a placeholder fixture explicitly labelled as non-case data and a fake `claude`.
- **Project settings** (`.claude/settings.json`) so headless stages run under `--permission-mode dontAsk`, with
  writes limited to `_workspace/`.

## Deliberate departures and interpretations

1. **The `response_measure` hint in `analysis.schema.json`.** The contract's description suggests
   `'unspecified (see gap G-x-y)'`. That conflicts with the normative rule that `G-*` ids appear only in gap
   records, and the rule wins. The harness requires `unspecified: ...` with no gap id, and the gap itself
   carries the scenario id.
2. **The evidence suffix is also applied** to approach descriptions and addressed-attribute rationales, and an
   `(evidence: AE-n)` citation is appended to sensitivity and tradeoff parameters. This preserves source references
   for every material finding. Only risk and non-risk rationales are required to use the exact suffix.
3. **Gap ids in the report.** The report's gap records have no id field (`additionalProperties: false`), so each
   description is prefixed `[G-x-n] (gap_type)`. That keeps the ids traceable and still inside gap records.
4. **Priority tuples** reach the report only when the inputs state them (observed with refs). Inferred priorities
   aren't representable, because the report tuple has no basis field and an unlabelled priority would read as a
   stakeholder judgment.
5. **Stage 5 is a deterministic projection.** The synthesizer agent runs it and reads the result back, and the
   gate requires an exact match, so every content correction goes through the single traceable revision in
   stage 7. The source's evaluate-architecture step 7 ("check before returning … revise") is carried out by
   stages 6 and 7, not inside synthesis.
6. **All six check categories block readiness** (structure, semantic_state, evidence_traceability,
   uncertainty, method_coverage, reference_boundary), as `check-evaluation` and `revise-report` list them.
   Heuristic lexicon checks (absence, performance attainment) can produce false positives. The reviser can
   resolve them only by rewording or relabelling toward uncertainty, which is always evidence-preserving.
7. **Metadata** is taken only from supplied `metadata`. A `system_name` that appears only in the prose
   description stays `null` rather than being extracted, so no metadata is ever inferred.

## Verification performed at generation time

- `hw check-bundle --target claude` was run on this bundle (see the generation transcript for its output).
- The self-tests (13) pass. They cover the clean run with no corrections (stage 7 still runs, readiness true), an
  absence labelled observed corrected by relabelling, an unmeasured performance claim leaving readiness
  false, a gap id in 04 failing the stage-4 gate, a stray write failing the scope gate, an edited draft failing
  the stage-5 gate, a reviewer check passed without any change failing the stage-7 gate, refusal of reference
  outputs, ledger order enforcement, and `source_refs` and suffix parsing.
- No live end-to-end run with a real model was performed: no case data was supplied, and none was invented.
