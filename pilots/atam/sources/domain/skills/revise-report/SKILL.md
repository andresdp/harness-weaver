---
name: revise-report
description: Apply one review pass of evidence-preserving corrections to an ATAM draft and recompute review readiness.
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
   Revalidate scenario lineage: report scenario IDs must remain unique, each analysis reference must resolve to the report scenario and match its text, and every scenario origin must remain traceable to trusted `evaluation_inputs`.
5. Write the final report and final review findings. Set `revision.applied` according to whether any content changed, list changed JSON locations, and list any remaining failed checks.
6. Compute `ready_for_architect_review` only now. It is false if any `fail` or `warn` remains for structure, semantic state, evidence traceability, uncertainty, method coverage, or reference boundary. It can be true only after this revision stage completes and none of those blocking findings remains.

If there were no corrections to make, still complete this stage, set `revision.applied: false`, and leave `changed_locations` and `remaining_failures` empty. Runtime completion does not change methodology state: the report remains a draft until a software architect records a review.
