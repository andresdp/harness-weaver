---
name: evaluate-architecture
description: Conduct an evidence-grounded ATAM evaluation from architecture inputs and produce a structured report.
---

# Evaluate Architecture with ATAM

Read the bundled `references/atam-methodology.yaml` and `references/atam-report-template.json` before analysis.

1. Establish scope, business drivers, architecture evidence, constraints, and open questions.
2. Refine quality attribute drivers into scenarios with stimuli, environments, responses, measurable response measures, and priority judgments when evidence supports them. Assign each scenario a stable ID and an origin record. Supplied scenarios use `raw_candidate_scenario`, the original source scenario ID, `observed` basis, and a source path to that item in `evaluation_inputs`. Derived scenarios use `derived_from_evidence` or `derived_from_driver`, a null source ID, `inferred` basis, and resolvable source paths into `evaluation_inputs`. Never cite `ground_truth_outputs`.
3. Identify architecture approaches only from supplied evidence. Mark inference explicitly.
4. Analyze prioritized scenarios against architecture decisions. Record risks, non-risks, sensitivity points, tradeoff points, rationale, and evidence.
5. Synthesize the report using the bundled `ATAM_Evaluation` template. Put generated findings under `evaluation_results`, preserve gaps and unknowns, and do not invent stakeholder workshop outcomes or measurements. Project each scenario's ID, text, primary quality attribute, and complete origin into `evaluation_results.scenarios`. Every analysis record must reference one of those report IDs and use matching scenario text.
6. Include `evaluation_results.semantic_state`. Assess context, drivers, and architecture evidence as `missing`, `partial`, or `sufficient`; assess scenario analysis as `not_started`, `partial`, or `reviewed`; assess report status as `not_started`, `draft`, or `reviewed`. Give evidence for every status, including evidence that an expected input is absent. Populate each material gap with its affected activity, missing evidence, and resolution question. Agent calls and completed pipeline stages are runtime facts, not methodology evidence. Keep the report status at `draft` until a software architect has reviewed it.
7. Ask the evidence reviewer to check method coverage, semantic-state evidence, and claim support before returning the report for architect review.
