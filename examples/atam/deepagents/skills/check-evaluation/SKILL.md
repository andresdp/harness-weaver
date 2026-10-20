---
name: check-evaluation
description: Check ATAM report structure, evidence traceability, method coverage, and explicit uncertainty.
---

# Check ATAM Evaluation

Read the bundled `references/atam-methodology.yaml` and `references/atam-report-template.json`.

Review the draft against the supplied inputs and output contract. Confirm generated findings are under `evaluation_results`, required report sections exist, and `evaluation_results.semantic_state` uses allowed values and includes evidence for each status. Keep the report status at `draft` unless a software architect has actually reviewed it. Check that each gap names its affected activity, missing evidence, and a resolution question. Confirm material claims have evidence or clear uncertainty labels, stakeholder priorities are not fabricated, and unknowns remain visible. Return corrections without adding unsupported facts.
