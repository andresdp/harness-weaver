---
name: check-evaluation
description: Check an ATAM report for required sections, evidence links, explicit uncertainty, and decision-use readiness.
---

# Check an ATAM Evaluation

Read `references/atam-methodology.yaml` and `references/atam-report-template.json`. Review a draft report against the supplied evaluation inputs and the ATAM output contract.

1. Confirm the output is rooted at `ATAM_Evaluation`, contains metadata and evaluation inputs, and places generated findings under `evaluation_results` with the report sections required by `references/atam-report-template.json`.
2. Trace each material finding to supplied evidence. Flag unsupported claims and missing references.
3. Check that quality attribute scenarios, priority judgments, and response measures distinguish evidence from assumptions.
4. Confirm gaps and unresolved questions are visible; do not treat missing reference data as a known answer.
5. Return findings and corrections. Mark the report ready for architect review only after structural and evidence checks pass.
