---
name: revise-report
description: "ATAM stage 5 (synthesize-and-review, revision): applies the review's fact-free corrections to 05_atam_report.json once, re-checks the corrected locations, and updates the revision record and readiness in 06_review_findings.json."
---

# Revise the Report Once (ATAM activity `synthesize-and-review`, revision)

## Objective

Apply the review's corrections a single time without adding facts, so that the architect receives the best draft the evidence allows, together with an honest record of what could not be fixed. Methodology profile: `/agent/skills/revise-report/references/methodology.yaml`. Contract: `/agent/skills/revise-report/references/atam-report.schema.json`.

## Input Artifacts

Read: `/artifacts/05_atam_report.json`, `/artifacts/06_review_findings.json`, and, for re-checking, `/artifacts/00_evaluation_inputs.json` … `/artifacts/04_analysis.json`.

## Procedure

1. If no check in `06_review_findings.json` has `result` `fail` or `warn`, set `revision` to `{"applied": false, "changed_locations": [], "remaining_failures": []}`, keep `ready_for_architect_review` as decided, and finish.
2. For each `fail` or `warn` check with a `correction`, apply it to `05_atam_report.json` only if it removes, re-labels, re-links or rephrases existing content. A correction that needs a new fact cannot be applied: leave the content and make sure a gap in `semantic_state.gaps` covers it.
3. Keep the report within the contract (no extra keys). Keep `report_status` = `draft` and `scenario_analysis_status` at most `partial`.
4. Re-check each corrected location against the stage artifacts, and update that check's `result` in `06_review_findings.json`.
5. Update `06_review_findings.json`: `revision.applied` = `true`, `changed_locations` = the JSON paths you changed, and `remaining_failures` = the ids of checks still `fail`. Recompute `ready_for_architect_review`: it is `true` only when no `structure`, `semantic_state`, `evidence_traceability` or `reference_boundary` check remains `fail`.

## Rules

- One revision pass only. Remaining failures stay visible for the architect; they are not hidden or argued away.
- **Correct:** check C-4 says "R-2 has no evidence" → remove R-2 from the report and record `...findings.risks[0]` in `changed_locations`.
- **Incorrect:** check C-4 says "R-2 has no evidence" → invent an evidence reference for R-2.

## Expected Output

Overwrite `/artifacts/05_atam_report.json` (same contract) and `/artifacts/06_review_findings.json` (same structure, with the updated `revision`, `checks[].result` and `ready_for_architect_review`). Read both files back and verify that they parse and conform to `/agent/skills/revise-report/references/atam-report.schema.json` and `/agent/skills/revise-report/references/review-findings.schema.json`.

Do not start a second review cycle and do not change any stage 1–4 artifact.
