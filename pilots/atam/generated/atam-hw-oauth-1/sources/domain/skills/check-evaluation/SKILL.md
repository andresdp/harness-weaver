---
name: check-evaluation
description: Check an ATAM report draft for required sections, evidence links, semantic-state evidence, explicit uncertainty and readiness for architect review.
---

# Check an ATAM Evaluation

Use the ATAM methodology profile (`methodology.yaml`) and the report contract (`atam-report.schema.json`). Review the draft against the supplied evaluation inputs.

1. Confirm the report is rooted at `ATAM_Evaluation`, contains metadata and evaluation inputs, and places generated findings under `evaluation_results` with every section the contract requires.
2. Confirm `evaluation_results.semantic_state` uses only the status values the methodology allows and gives evidence for each status. The report stays at `draft` unless a software architect has actually reviewed it. Each gap names its affected activity, missing evidence and a resolution question.
3. Trace each material finding to supplied evidence, and flag unsupported claims and missing references. Each analysis record must reference a source scenario by id or verbatim text.
4. Check that quality attribute scenarios, priority judgments and response measures distinguish evidence from assumptions.
5. Confirm gaps and unresolved questions stay visible. Missing reference data is never treated as a known answer.
6. Return findings and corrections without adding unsupported facts. Mark the report ready for architect review only after structural and evidence checks pass.
