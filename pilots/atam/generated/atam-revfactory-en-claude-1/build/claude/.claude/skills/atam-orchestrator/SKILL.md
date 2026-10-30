---
name: atam-orchestrator
description: "Runs an evidence-grounded ATAM architecture evaluation of a supplied software architecture through the ordered stage pipeline (intake, context, utility tree, approaches, scenario analysis, report draft, review, single revision) and returns a draft report for architect review. Use when asked to evaluate an architecture with ATAM, run an architecture evaluation, produce an ATAM report, assess risks, tradeoffs or sensitivity points of a described architecture, and for follow-ups: re-run, run again, resume, update, fix, redo only the scenario analysis (or any stage), re-review or revise the report, improve the results based on the previous run. Not for answering general ATAM questions, reviewing an existing report you were handed without running the pipeline (use check-evaluation directly), or facilitating stakeholder workshops."
---

# ATAM Evaluation Orchestrator

## Execution mode: code-ordered stage pipeline (sub-agent per stage)

The order is fixed in code, not left to judgment in the moment. `atam_harness/run.py` runs `stage0-intake`
deterministically, then starts each of the seven model stages as its **own** headless invocation
(`claude -p --agent <stage-agent>`). Between invocations, `atam_harness/atam.py` gates each stage. The gate
checks the artifact schema, cross-artifact identifiers, `source_refs` resolution and write scope, and records
the stage in `_workspace/run_ledger.json`. A stage cannot begin until every earlier stage has completed and
its outputs are unchanged. `stage7-revise_report` runs on every run, after `stage6-check_evaluation`. Only
stage 7 (`atam.py finalize`) computes `ready_for_architect_review`.

The stage agents don't talk to each other. Data passes only through files, and each stage has exactly one
runtime invocation per attempt, so stages 5, 6 and 7 can't be merged or skipped by a single model response.

| Stage | Agent (`subagent_type`) | Skill | Reads | Writes only |
| --- | --- | --- | --- | --- |
| `stage0-intake` | deterministic (`atam.py intake`) | — | user input JSON | `00_evaluation_inputs.json` |
| `stage1-establish_context` | `atam-context-analyst` (sonnet) | evaluate-architecture | 00 | `01_context.json` |
| `stage2-build_utility_tree` | `atam-utility-tree-builder` (opus) | evaluate-architecture | 00–01 | `02_utility_tree.json` |
| `stage3-identify_approaches` | `atam-approach-analyst` (opus) | evaluate-architecture | 00–02 | `03_approaches.json` |
| `stage4-analyze_scenarios` | `atam-scenario-analyst` (opus) | evaluate-architecture | 00–03 | `04_analysis.json` |
| `stage5-synthesize_report` | `atam-report-synthesizer` (sonnet) | evaluate-architecture | 00–04 | `05_atam_report_draft.json` |
| `stage6-check_evaluation` | `atam-evaluation-checker` (opus) | check-evaluation | 00–05 draft | `06_review_findings_initial.json` |
| `stage7-revise_report` | `atam-report-reviser` (opus) | revise-report | 00–06 initial | `05_atam_report.json`, `06_review_findings.json` |

All paths are relative to `_workspace/` under the project root. The final outputs are
`_workspace/05_atam_report.json` and `_workspace/06_review_findings.json`. Intermediate artifacts, the ledger and
per-stage logs (`_workspace/.runtime/`) are kept so the run can be audited later.

## Procedure

### Step 0: Check existing work

1. Check whether `_workspace/run_ledger.json` exists. If it does, run `python3 atam_harness/atam.py status`.
2. Decide the run mode:
   - **No workspace, or the user supplies a new input**: do a new run (step 2). Intake moves any existing
     workspace to `_workspace_archive/<previous run_id>/`. Nothing is deleted.
   - **Same input, and the user wants one part redone** ("redo the scenario analysis", "re-review", "revise
     again"): run `python3 atam_harness/run.py --from <stage-id>`. That stage and every later stage are
     invalidated, their outputs move to `_workspace/.runtime/superseded/`, and they run again in order.
     Re-reviewing means `--from stage6-check_evaluation`. Revising again means `--from stage7-revise_report`.
   - **Interrupted run** (a stage is started or failed): run `python3 atam_harness/run.py --resume`.

### Step 1: Confirm the input

1. Ask the user for the path to the evaluation inputs if it wasn't given. The input is a template-shaped JSON
   object: `ATAM_Evaluation.evaluation_inputs` (plus optional `title` and `metadata`), as in
   `.claude/skills/evaluate-architecture/references/atam-report-template.json`, or the same object without
   the `ATAM_Evaluation` wrapper.
2. Don't search the filesystem for case data, and don't create, complete or "improve" inputs. Missing
   information becomes gaps in the run.
3. If the file contains `ground_truth_outputs` or other reference answers, intake refuses it. Ask the user
   for an input-only copy. Don't strip it yourself, because reading it would already cross the reference
   boundary.

### Step 2: Run the pipeline

Run `python3 atam_harness/run.py --input <path>` with Bash in the background. It takes several minutes per
stage. Wait for the completion notification, and don't guess the outcome before it arrives. Useful options:
`--run-id <session id>` (shown in the report title), `--claude-arg=--model=<m>` (override every stage's model),
and `--dry-run` (print the plan only).

Exit codes: 0 means the pipeline finished (check readiness in step 3). 2 means a stage failed its gate twice and
later stages were not run. 3 means a ledger order or state refusal. 4 means a non-retryable runtime failure
(usage limit, authentication, permission), recorded in `_workspace/.runtime/blocked.md`.

#### Fallback: the session cannot start headless `claude -p`

Use this only when `run.py` can't execute `claude`. Drive the same ledger with one `Agent` call per stage.
Run them strictly one at a time, never in parallel and never two stages in one call:

First run `python3 atam_harness/atam.py intake --input <path> --run-id <id>` (stage 0). Then, for each row
below in order, with none skipped and stage 7 always included:

1. `python3 atam_harness/atam.py stage begin <stage-id> --invocation agent-tool`
2. `python3 atam_harness/atam.py stage-prompt <stage-id>` gives you the prompt (PROMPT).
3. Make the Agent call shown in the row, with `run_in_background: false`.
4. `python3 atam_harness/atam.py stage complete <stage-id>`
5. On a gate failure, run `stage begin <stage-id> --retry --invocation agent-tool` and call the same agent
   once more with PROMPT plus the gate errors printed by `stage complete`. Stop if it fails again.

| Stage id | Agent call |
| --- | --- |
| `stage1-establish_context` | `Agent(subagent_type: "atam-context-analyst", prompt: PROMPT)` |
| `stage2-build_utility_tree` | `Agent(subagent_type: "atam-utility-tree-builder", prompt: PROMPT)` |
| `stage3-identify_approaches` | `Agent(subagent_type: "atam-approach-analyst", prompt: PROMPT)` |
| `stage4-analyze_scenarios` | `Agent(subagent_type: "atam-scenario-analyst", prompt: PROMPT)` |
| `stage5-synthesize_report` | `Agent(subagent_type: "atam-report-synthesizer", prompt: PROMPT)` |
| `stage6-check_evaluation` | `Agent(subagent_type: "atam-evaluation-checker", prompt: PROMPT)` |
| `stage7-revise_report` | `Agent(subagent_type: "atam-report-reviser", prompt: PROMPT)` |

The ledger refuses out-of-order `begin` calls, rejects writes outside each stage's files, and lets only
stage 7's `finalize` produce readiness. If you skip or merge a stage, the run has no valid final artifact.

### Step 3: Report the result

1. Read `_workspace/06_review_findings.json` and `_workspace/05_atam_report.json`. Don't change them.
2. Tell the user:
   - `ready_for_architect_review` and its `remaining_failures`, with check ids and what each one means;
   - how many risks, non-risks, sensitivity points and tradeoff points there are, and their basis mix
     (observed versus inferred);
   - the material gaps and their resolution questions, which are the questions for the architect;
   - that `report_status` is `draft` and a software architect familiar with the system must review it
     before it informs any decision.
3. When quoting findings, keep their `(evidence: …; basis: …)` suffix. Never present an inferred finding as
   observed fact.

## Error handling

| Situation | Response |
| --- | --- |
| A stage gate fails | `run.py` retries once with the gate errors in the prompt. If it fails again it stops (exit 2), and later stages don't run. Report the stage and its errors (`atam.py status`, `run_ledger.json`), then offer `--resume` after the cause is fixed. |
| Usage limit, expired authentication, denied permission (exit 4) | Don't retry, because it would fail the same way. Read `.runtime/blocked.md` and the ledger to see how far the run got, tell the user, and give the reset time for usage limits. Resume with `--resume` once the cause is resolved. |
| Intake refused (reference outputs, wrong shape) | Ask the user for a corrected input-only file. Never edit the input yourself. |
| A stage agent's output looks wrong but passed its gate | Don't patch it by hand. Re-run that stage with `--from <stage-id>` and include the user's feedback, or let stages 6 and 7 record and correct it. |
| Readiness is false | This is a valid outcome, not an error. Report the remaining findings and the facts they need. If the user can supply missing facts, that means a corrected input and therefore a new run. `--from stage7-revise_report` helps only when the remaining items could be fixed by rewording, without new facts. |

The orchestrator only reports facts it has read in the artifacts. It never fills a stopped stage's judgments by guesswork.

## Test scenarios

### Normal flow
1. The user gives `case.json` (template-shaped, no reference outputs). Step 0 finds no workspace.
2. `run.py --input case.json` completes stages 0–7 in ledger order. The initial review has no warn or fail. Stage 7 still runs: `revision.applied: false`, `ready_for_architect_review: true`.
3. Report readiness, the findings with their evidence suffixes, the gaps, and the draft status.

### Correction flow
1. Stage 6 flags `UNC-ABSENCE-BASIS` (a risk drawn from absence was labelled observed) and a reviewer `UNC-R1` (unmeasured latency described as "adequate").
2. Stage 7 relabels the risk to `basis: inferred` and rephrases the latency claim as undeterminable. Finalize re-runs the checks, and both now pass. `changed_locations` lists both pointers, and readiness is true.

### Error flow
1. Stage 4 writes `response_measure: "unspecified (see gap G-2-1)"`. The gate fails because a gap id appears outside a gap record.
2. The retry prompt carries the error. The agent rewrites it as `unspecified: no response measure supplied`, and the gate passes.
3. If it had failed again, the run would stop at stage 4 (exit 2) with no draft, and you would report that.

### Blocked flow
1. Stage 3 hits a usage limit. `run.py` exits 4 and writes `.runtime/blocked.md`.
2. Report that stages 0–2 completed and stage 3 is blocked, with the reset time. Later, `run.py --resume` continues stage 3 as a retry.

The harness self-tests (`python3 -m unittest discover -s atam_harness/tests`) exercise these flows with a fake `claude` and a placeholder fixture.
