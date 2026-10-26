---
name: revise-report
description: Apply one review pass of evidence-preserving corrections to an ATAM draft and recompute review readiness. In this harness it is the stage7-revise_report procedure used by the atam-report-reviser agent; it reads 05_atam_report_draft.json and 06_review_findings_initial.json and writes only 05_atam_report.json and 06_review_findings.json, running atam.py finalize to compute ready_for_architect_review. Runs on every evaluation run, including when nothing needs correcting.
---

# Revise an ATAM Report Draft

This is a required workflow step after `check-evaluation`. It must run as its own ordered runtime stage, after the draft and initial review artifact exist. Do not fold it into report synthesis or review as an optional checklist item.

## Inputs

Read the synthesized draft, the initial review findings, all source and intermediate artifacts, and their schemas. Do not read evaluator-only reference outputs.

## Procedure

1. Read every review check with result `fail` or `warn` and its correction.
2. Apply each correction that can be made by removing, relabeling, relinking, or rephrasing existing content without inventing facts. Keep `report_status: draft` and `scenario_analysis_status` at most `partial`.
3. If a correction needs missing facts, leave the affected conclusion qualified or unresolved and preserve a gap; do not fabricate a replacement.
4. Recheck each changed location against the source and intermediate artifacts. Update the final review finding to `pass` only when the correction resolves the concern; otherwise retain `fail` or `warn` and explain what remains.
5. Write the final report and final review findings. Set `revision.applied` according to whether any content changed, list changed JSON locations, and list any remaining failed checks.
6. Compute `ready_for_architect_review` only now. It is false if any `fail` or `warn` remains for structure, semantic state, evidence traceability, uncertainty, method coverage, or reference boundary. It can be true only after this revision stage completes and none of those blocking findings remains.

If there were no corrections to make, still complete this stage, set `revision.applied: false`, and leave `changed_locations` and `remaining_failures` empty. Runtime completion does not change methodology state: the report remains a draft until a software architect records a review.

## Harness binding (stage7-revise_report)

The protocol above is normative. Steps 5 and 6 are carried out by code so the result can't drift: you
write the content, and `atam.py finalize` writes `revision` and `ready_for_architect_review`.

**Reads:** `_workspace/00_evaluation_inputs.json` through `04_analysis.json`, `05_atam_report_draft.json`,
`06_review_findings_initial.json`, and the contracts.
**Writes only:** `_workspace/05_atam_report.json` and `_workspace/06_review_findings.json`. The draft and the
initial review are frozen. The gate rejects any change to them.

### Procedure

1. Run `python3 atam_harness/atam.py start-final`. It copies the draft to `05_atam_report.json`. Make every
   correction in that file with Edit, and keep each change as small as possible.
2. For each `warn` or `fail` in the initial review, in both automated and reviewer checks:
   - **Relabel**: change `basis: observed` to `basis: inferred` in the rationale suffix when the conclusion is
     reasoned or drawn from absence. Never relabel inferred to observed.
   - **Relink**: drop a cited id that doesn't support the claim. Cited ids must stay a subset of the finding's
     ids in `04_analysis.json`, and you can't add new evidence ids.
   - **Rephrase or qualify**: turn "violates" or "is adequate" into "cannot be determined without <measure>", and
     turn "there is no X" into "the supplied material does not describe X".
   - **Remove**: delete an unsupported finding, decision or claim entirely.
   - Keep the exact suffix ` (evidence: AE-1, AE-2; basis: observed|inferred)` at the end of every risk and
     non-risk rationale. Never put a `G-*` id anywhere outside `semantic_state.gaps`.
   - Never add findings, approaches, scenarios, measures, priorities, attendees or metadata, and never edit
     `evaluation_inputs`. Don't drop any gap. You may add a gap record (description prefix `[G-7-n]`) when a
     correction leaves something unresolved.
3. Run `python3 atam_harness/atam.py check --report _workspace/05_atam_report.json --phase final` to re-check
   the automated results on the revised report.
4. Write `_workspace/06_review_findings.json` with `review_stage: "final"`, `run_id`,
   `reviewed_report: "05_atam_report.json"`, and `checks` holding **every reviewer check** from the initial
   review, with the same `check_id` and `location`. For each one, set the updated `result` and a
   `resolution` saying what you changed, or why the issue remains. Mark a check `pass` only if your edit
   resolved it. The gate rejects a `pass` when nothing changed at the check's location. You may omit the
   automated checks and the `summary`, because finalize regenerates them.
5. Run `python3 atam_harness/atam.py finalize`. It re-runs the automated checks on the final report, merges
   your reviewer checks, computes `revision` (`applied`, `changed_locations` from a JSON diff of draft versus
   final, `remaining_failures`), verifies the stage order in the run ledger, and sets
   `ready_for_architect_review`, which is true only when no warn or fail remains in any blocking category.
   Never write or edit these fields yourself.
6. Run `python3 atam_harness/atam.py validate stage7-revise_report`. If it reports problems, fix the report or
   your reviewer checks, then run finalize and validate again.

If the initial review has no warn or fail, still run steps 1, 4, 5 and 6. The result is `revision.applied:
false`, and readiness is computed from the clean checks. A run that skips this stage has no final report and
no readiness value at all.
