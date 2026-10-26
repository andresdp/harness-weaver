---
name: check-evaluation
description: Check ATAM report structure, evidence traceability, method coverage, and explicit uncertainty.
---

# Check ATAM Evaluation

Read the bundled `references/atam-methodology.yaml` and `references/atam-report-template.json`.

Review the draft against the supplied inputs and output contract. Confirm generated findings are under `evaluation_results`, required report sections exist, and `evaluation_results.semantic_state` uses allowed values and includes evidence for each status. Keep the report status at `draft` unless a software architect has actually reviewed it. Check that each gap names its affected activity, missing evidence, and a resolution question. Confirm material claims have evidence or clear uncertainty labels, stakeholder priorities are not fabricated, and unknowns remain visible.

Validate scenario lineage before readiness: report scenarios have unique stable IDs; each origin has the correct kind, basis, source scenario ID and non-empty `source_refs`; every source path resolves against trusted `evaluation_inputs` and excludes `ground_truth_outputs`; and each analysis reference ID and text match one report scenario. Any missing, duplicate, dangling or unresolvable lineage blocks readiness. Return corrections without adding unsupported facts.
