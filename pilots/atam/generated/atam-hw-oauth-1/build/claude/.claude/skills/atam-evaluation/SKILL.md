---
name: atam-evaluation
description: "Runs an evidence-grounded ATAM (Architecture Tradeoff Analysis Method) evaluation of a supplied software architecture and produces a draft JSON report (ATAM_Evaluation) plus review findings for a software architect. MUST be used when the user asks to evaluate an architecture with ATAM, build a utility tree, identify risks, non-risks, sensitivity or tradeoff points for an architecture case, or produce an ATAM report from evaluation inputs. Also use it for follow-ups: re-run or redo a stage (e.g. 'redo only the utility tree', 're-analyze the scenarios'), revise or update a previous ATAM report, re-check a draft, or record an architect's review of the draft. Do not use it for general architecture advice without an evaluation input, or for writing ADRs."
---

# ATAM Evaluation Orchestrator

Coordinates the five-stage ATAM pipeline defined by the HarnessSpec `archeval-atam-harness`. The output is a **draft** for a software architect's review, not a decision and not a simulated stakeholder workshop.

## Execution mode: Sub-agent delegation

Each stage is a one-shot custom agent (`subagent_type`), invoked with the `Agent` tool and no `name`. Agents never message each other: all data passes through JSON files in `_workspace/`. Stages 2 and 3 depend only on stage 1, so they run in parallel (two `Agent` calls in one message). All other stages run in order. You, the main agent, run the deterministic validator between stages and never write stage artifacts yourself.

## Agent configuration

| Stage (methodology activity) | `subagent_type` | Skill | Reads | Writes |
|---|---|---|---|---|
| 1 establish-context | `atam-context-analyst` | `atam-establish-context` | 00 | `_workspace/01_context.json` |
| 2 build-utility-tree | `atam-utility-tree-analyst` | `atam-build-utility-tree` | 00, 01 | `_workspace/02_utility_tree.json` |
| 3 identify-approaches | `atam-approach-analyst` | `atam-identify-approaches` | 00, 01 | `_workspace/03_approaches.json` |
| 4 analyze-scenarios | `atam-scenario-analyst` | `atam-analyze-scenarios` | 00–03 | `_workspace/04_analysis.json` |
| 5a synthesize-and-review (draft, revise) | `atam-report-synthesizer` | `atam-synthesize-report` | 00–04 (+06 when revising) | `_workspace/05_atam_report.json` |
| 5b synthesize-and-review (review) | `atam-evaluation-reviewer` | `check-evaluation` | 00–05 | `_workspace/06_review_findings.json` |

Validator: `python3 .claude/skills/check-evaluation/scripts/validate_artifacts.py` (standard library only). Below it is written as `VALIDATE`. Its exit codes: 0 = pass (warnings allowed), 1 = failures, 2 = usage or missing file, 3 = reference-boundary violation.

## Procedure

### Step 0: Check for existing work

1. If `_workspace/` does not exist, run from scratch.
2. If `_workspace/` exists and the user supplies a **new input file**, move it to `_workspace_<YYYYMMDD-HHMMSS>/` and run from scratch.
3. If `_workspace/` exists and the user asks for a **partial re-run**, re-run the named stage and every stage downstream of it, keeping the upstream artifacts:

   | Re-run requested | Stages to run |
   |---|---|
   | context | 1, 2, 3, 4, 5 |
   | utility tree / scenarios / priorities | 2, 4, 5 |
   | approaches | 3, 4, 5 |
   | scenario analysis / risks / tradeoffs | 4, 5 |
   | report wording or a re-check | 5 |

   Pass the user's feedback and the existing artifact path to the re-run agent (see Re-invocation in its definition).
4. If the user supplies an **architect's review** of a finished draft, go to "Follow-up: record an architect review".

### Step 1: Bind the input port (main agent)

1. Get the case input file path from the user's request. If none was given, ask for it. The harness has no built-in case data.
2. Run `VALIDATE prepare-input <input-path> _workspace`.
   - Exit 3: stop. Tell the user the file contains evaluator-only reference outputs (`ground_truth_outputs`) or generated results, and ask for an input-only copy. Do not open or summarize the file's reference content.
   - Exit 1 or 2: report the printed error and stop.
   - Exit 0: `_workspace/00_evaluation_inputs.json` exists. From now on, every agent reads only the workspace, never the original file.

### Step 2: Stage 1 (establish context)

Invoke `Agent(subagent_type: "atam-context-analyst", description: "ATAM stage 1 context", prompt: ...)` with this prompt: the workspace path, the instruction "Use skill atam-establish-context; read _workspace/00_evaluation_inputs.json; write _workspace/01_context.json", and any user feedback. Then run `VALIDATE check _workspace --stage 1`.

### Step 3: Stages 2 and 3 in parallel

In **one message**, invoke `atam-utility-tree-analyst` (skill `atam-build-utility-tree`, writes `02_utility_tree.json`) and `atam-approach-analyst` (skill `atam-identify-approaches`, writes `03_approaches.json`). Wait for both completion notifications, then run `VALIDATE check _workspace --stage 3`.

### Step 4: Stage 4 (analyze scenarios)

Invoke `atam-scenario-analyst` (skill `atam-analyze-scenarios`, writes `04_analysis.json`). Then run `VALIDATE check _workspace --stage 4`.

### Step 5: Stage 5 (synthesize, review, one revision)

1. Invoke `atam-report-synthesizer` (skill `atam-synthesize-report`, writes `05_atam_report.json`). Run `VALIDATE check _workspace --stage 5`.
2. Invoke `atam-evaluation-reviewer` (skill `check-evaluation`, writes `06_review_findings.json`, first pass).
3. If `06_review_findings.json` has any `fail` or `warn` check, invoke `atam-report-synthesizer` again in revision mode, passing `_workspace/06_review_findings.json`. Run `VALIDATE check _workspace --stage 5`. Then invoke `atam-evaluation-reviewer` for the second pass, passing the synthesizer's list of changed locations and the corrections it could not apply. Run at most **one** revision cycle; remaining failures stay visible.
4. Run `VALIDATE check _workspace --stage 6`.

### Step 6: Deliver and hand over to the architect (human gate H1)

1. Copy `_workspace/05_atam_report.json` to the output path the user named, default `output/atam_report.json`, and `_workspace/06_review_findings.json` to `output/review_findings.json`. Keep `_workspace/` for traceability.
2. Report to the user, reading every value from the artifacts, not from agent messages:
   - the five `semantic_state` values, with one evidence line each;
   - counts of scenarios, analyzed records, risks, non-risks, sensitivity points, tradeoff points and gaps;
   - `ready_for_architect_review`, the remaining failing checks and `architect_review_focus`;
   - the final validator summary line.
3. State plainly: **the report is a draft (`report_status` = `draft`). A software architect familiar with the evaluated system must review method coverage, evidence grounding, risks, tradeoffs and unknowns before it informs any decision.** Runtime completion of this pipeline is not ATAM progress.

### Follow-up: record an architect review

Do this only when the user supplies an actual review by a software architect: reviewer role (a name is optional), date, what was reviewed (report, scenario analysis or both), the outcome, and any corrections.

1. Write `_workspace/architect_review.json`: `{"reviewer_role": ..., "reviewer": ... or null, "date": ..., "scope": ["report", "scenario_analysis"], "outcome": ..., "corrections": [...]}`, recording only what the user stated.
2. If corrections were given, re-run the affected stages (Step 0 table) and pass the corrections as feedback.
3. Invoke `atam-report-synthesizer` to set `report_status` (and `scenario_analysis_status`, if the scope includes it) to `reviewed`, with evidence citing `architect_review.json`. Run `VALIDATE check _workspace --stage 6` and deliver as in Step 6.

Never set `reviewed` on your own judgment, on the reviewer agent's judgment, or because the pipeline finished.

## Error handling

| Situation | Response |
|---|---|
| Validator reports `FAIL` after a stage | Re-invoke the same agent **once**, passing the exact `FAIL` lines and the existing artifact path. If it still fails, stop the pipeline, keep `_workspace/`, and report the failing stage and lines. Never patch a stage artifact yourself or run later stages on a failed one. |
| Agent returns without writing its artifact | Treat it as a failure: retry once with the same prompt plus "the artifact was not written". Then stop as above. |
| Agent reports a reference-boundary violation | Stop immediately and ask the user for an input-only copy. Do not retry. |
| Usage limit, expired authentication or denied permission | Do not retry. Inspect `_workspace/` to see which artifacts exist, write `_workspace/run_status.md` listing the completed and missing stages, and tell the user. For a usage limit, also say when it resets. |
| Stage 2 or 3 fails while the other succeeds | Keep the successful artifact; retry only the failed stage. |
| Reviewer still reports failures after the revision cycle | Deliver anyway, with `ready_for_architect_review` = `false`; list the remaining failures prominently in the hand-over. |
| Conflicting statements in the inputs | They stay side by side as separate items plus a `conflict` gap; nobody resolves them silently. |

When you report on a stalled agent, state only facts you verified in the files. Never guess the agent's judgment calls.

## Data layout

```
_workspace/
  00_evaluation_inputs.json   input port (normalized by prepare-input)
  01_context.json             stage 1
  02_utility_tree.json        stage 2
  03_approaches.json          stage 3
  04_analysis.json            stage 4
  05_atam_report.json         stage 5 draft (contract: atam-report.schema.json)
  06_review_findings.json     stage 5 review
  architect_review.json       only after a real architect review
output/
  atam_report.json, review_findings.json
```

## Test scenarios

### Happy path
1. The user says "Run an ATAM evaluation of `cases/x/inputs.json`". `prepare-input` exits 0.
2. Stages 1–4 pass the validator on the first try; stages 2 and 3 run in parallel.
3. The synthesizer drafts 05, the reviewer finds two `warn` checks, one revision is applied, the second pass passes, and the `--stage 6` validation exits 0.
4. Expected: `output/atam_report.json` with `report_status` = `draft`, every stage gap present, and a hand-over naming the architect review focus.

### Error path: reference leak
1. The input file contains `ATAM_Evaluation.ground_truth_outputs`.
2. `prepare-input` exits 3, and no agent is invoked.
3. Expected: the user is asked for an input-only copy, and no reference content is echoed.

### Error path: stage failure
1. `VALIDATE check _workspace --stage 4` reports `FAIL [V3] ... approach AP-7 not in 03_approaches.json`.
2. `atam-scenario-analyst` is re-invoked once with that line; it fails again.
3. Expected: the pipeline stops after stage 4, `_workspace/` is kept, and the user sees the failing lines. No report is produced from a broken analysis.
