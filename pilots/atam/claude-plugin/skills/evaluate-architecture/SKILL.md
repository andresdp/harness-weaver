---
name: evaluate-architecture
description: Conduct an evidence-grounded ATAM evaluation of a supplied software architecture and produce a structured report.
argument-hint: "[architecture description or evaluation input file]"
---

# Evaluate an Architecture with ATAM

Read `references/atam-methodology.yaml` and `references/atam-report-template.json` before analysis. The report uses `evaluation_results` for generated findings; never copy the dataset's `ground_truth_outputs` into generation context. The method is an inspectable, bounded prototype; it does not claim to replace a facilitated stakeholder workshop.

## Input

Read the supplied architecture description, business context, constraints, and evaluation questions. When the input is a dataset JSON, select and read only `ATAM_Evaluation.evaluation_inputs`; do not load the full document and do not read `ground_truth_outputs` or other reference answers into the analysis context. If the runtime cannot select that field without loading the full document, ask for an evaluation-input-only copy.

## Workflow

1. Establish system scope, business drivers, architecture evidence, and open questions. If essential context is missing, ask the architect or record the gap before proceeding.
2. Ask the quality attribute analyst to refine drivers into scenarios and create a utility tree. Keep unsupported priorities unresolved. Give every scenario a stable report ID and preserve its origin. Supplied raw scenarios use `kind: raw_candidate_scenario`, the original source ID, `basis: observed`, and a source path into `evaluation_inputs.raw_candidate_scenarios`. Derived scenarios use `derived_from_evidence` or `derived_from_driver`, a null source ID, `basis: inferred`, and resolvable source paths into `evaluation_inputs`. Do not cite `ground_truth_outputs`.
3. Ask the analyst to identify architecture approaches from source evidence and analyze the prioritized scenarios.
4. Keep semantic progress in the final report's `evaluation_results.semantic_state`. Assess `context_status`, `driver_status`, and `architecture_evidence_status` as `missing`, `partial`, or `sufficient`; assess `scenario_analysis_status` as `not_started`, `partial`, or `reviewed`; assess `report_status` as `not_started`, `draft`, or `reviewed`. Give evidence for every status, including evidence that an expected input is absent. Record unresolved items with all four gap fields from the template. Do not equate completed agent calls with completed methodology activities. Keep `report_status` at `draft` until a software architect has reviewed the report.
   Keep intermediate artifacts as structured notes in the active evaluation context; do not create standalone files. Incorporate their findings into the final report.
5. Assemble a JSON report rooted at `ATAM_Evaluation` and conforming to `references/atam-report-template.json`. Put generated findings under `evaluation_results`. Project each scenario's ID, text, primary quality attribute, and complete origin unchanged into `evaluation_results.scenarios`. Each analysis record references the stable report scenario ID and uses matching scenario text. Include only evidence-backed findings; use the report's rationale fields to explain reasoning. Record assumptions and unresolved items in the narrative response if the template cannot represent them.
6. Ask the evidence reviewer to check coverage, claim support, assumptions, and unknowns. Revise the report where needed.
7. Return the report and ask a software architect to review it before decision use.

## Method boundaries

- Do not invent stakeholder priorities or workshop outcomes.
- Distinguish observed architecture decisions from inferred approaches.
- A missing response measure is an open issue, not an invitation to fabricate a threshold.
- Report risks, non-risks, sensitivity points, and tradeoff points only when supported by the input.
- Preserve source references for every material finding where the supplied input permits.
