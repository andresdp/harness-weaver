---
name: synthesize-report
description: "ATAM stage 5 (synthesize-and-review, drafting): projects 00–04 into the contract-conforming ATAM report rooted at ATAM_Evaluation (metadata, original evaluation inputs, utility tree, approaches, analysis records, scenarios, semantic state, gaps) with report_status kept at draft, and writes 05_atam_report.json."
---

# Synthesize the ATAM Report (ATAM activity `synthesize-and-review`, drafting)

## Objective

Assemble the report draft the architect will review. It contains only what stages 1–4 established, conforms exactly to the report contract, and keeps every gap visible. This is a projection, not new analysis. Method basis: steps 5–6 of `/agent/skills/synthesize-report/references/evaluate-architecture.md`. Contract: `/agent/skills/synthesize-report/references/atam-report.schema.json`, with the human-readable `/agent/skills/synthesize-report/references/atam-report-template.json`. Methodology profile: `/agent/skills/synthesize-report/references/methodology.yaml`.

## Input Artifacts

Read: `/artifacts/00_evaluation_inputs.json`, `/artifacts/01_context.json`, `/artifacts/02_utility_tree.json`, `/artifacts/03_approaches.json`, `/artifacts/04_analysis.json`.

## Evidence conventions (shared by every ATAM stage)

- **Allowed sources.** Use only `/artifacts/00_evaluation_inputs.json` and the upstream artifacts listed under Input Artifacts. Never read or request reference evaluation outputs (`ground_truth_outputs`) or any earlier evaluation of the same system. They are evaluator-only.
- **`source_refs`** are JSON paths into `00_evaluation_inputs.json`. They start at `evaluation_inputs`, `metadata` or `title` and use the exact keys present, for example `evaluation_inputs.business_context.business_goals[0]` or `evaluation_inputs.quantitative_model_parameters["network bandwidth"]`. Before writing a path, confirm it exists in the input.
- **`basis`**: `observed` means the input states it (cite at least one `source_ref`). `inferred` means it is reasoned from cited inputs (cite them and state the reasoning). `assumption` means the inputs do not support it, so it must also be recorded as a gap of type `assumption`. Never present an inference or an assumption as observed.
- **IDs** are stable within a run and are how artifacts link: `BD-n` business drivers, `AE-n` architecture evidence, `Q-n` open questions, scenario ids, `AP-n` approaches, `AR-n` analysis records, `R-n`/`NR-n`/`S-n`/`T-n` findings and `G-<stage>-<n>` gaps. Link by ID, never by paraphrase.
- **Gaps** record what is unknown, conflicting, incomplete or assumed: `{"id": "G-<stage>-<n>", "gap_type": "unknown|conflict|incomplete|assumption", "description": "...", "affected_activity": "<activity id>", "missing_evidence": "...", "resolution_question": "..."}`. Activity ids: `establish-context`, `build-utility-tree`, `identify-approaches`, `analyze-scenarios`, `synthesize-and-review`. A gap is a finding, not a failure. Missing evidence never licenses invention.
- **Status evidence** names observed facts about the inputs or artifacts, including absences, for example `"evaluation_inputs has no phase_2_architectural_context key"` or `"evaluation_inputs.raw_candidate_scenarios has 6 entries; 2 state a measurable response"`. Agent activity ("task completed", "stage ran") is never evidence of methodology progress.

## Procedure

1. **Readiness.** All of 00–04 must exist. If one is missing, stop and report which one; never synthesize around a missing stage.
2. **Root and header.** The document is `{"ATAM_Evaluation": {...}}`. `title`: the input's `title` if present, otherwise `"ATAM Evaluation — <metadata.system_name or 'unnamed system'> — draft"`. `metadata`: copy `01_context.json.metadata` unchanged.
3. **`evaluation_inputs`**: copy `00_evaluation_inputs.json.evaluation_inputs` **exactly**, with no edits, reordering of values, summaries or additions.
4. **`evaluation_results`**, built only from the stage artifacts. The contract forbids extra keys, so evidence travels inside the text fields:
   - `utility_tree`: `root` = `"Utility"`; for each node, `attribute_name` and `children`, each child with only `refinement`, `scenario_id`, `scenario_description` and `priority_tuple` (`null` stays `null`).
   - `architectural_approaches`: from `03_approaches.json`: `approach_name`; `description` + ` (evidence: AE-…)` + for inferred approaches ` [inferred: <inference_note>]`; `addressed_attributes` unchanged.
   - `analysis_records`: one per `04_analysis.json` record, in the same order: `scenario_reference`, `quality_attribute`, `environment`, `stimulus`, `response_measure`, `architectural_decisions`; `reasoning` + ` (approaches: AP-…; evidence: AE-…)`. For `findings`, keep each finding's `id`; risks and non-risks keep `description`, and `rationale` gets ` (evidence: …; basis: observed|inferred)` appended; sensitivity points keep `parameter` + ` (evidence: …)` and `correlated_attribute`; tradeoff points keep `parameter` + ` (evidence: …)` and `conflicting_attributes`. Drop `record_id`, `scenario_id`, `approach_ids`, `evidence_ids` and `basis` as separate keys.
   - `scenarios`: from `02_utility_tree.json.scenarios`, with only `scenario_text` and `primary_quality_attribute`.
5. **`semantic_state`**:
   - `context_status`: from `01_context.json`.
   - `driver_status`: from `02_utility_tree.json` (the refined assessment); add the 01 evidence when it is still relevant.
   - `architecture_evidence_status`: from `03_approaches.json` (refined), plus relevant 01 evidence.
   - `scenario_analysis_status`: from `04_analysis.json` (`not_started` or `partial`).
   - `report_status`: `{"value": "draft", "evidence": ["05_atam_report.json assembled from 01–04; no architect review is recorded"]}`.
   - `gaps`: **every** gap from 01, 02, 03 and 04, in stage order. Each keeps `affected_activity`, `missing_evidence` and `resolution_question` unchanged, and its `description` becomes `"[<gap_type>] <original description> (<gap id>)"`. Add a `synthesize-and-review` gap only for a problem found while assembling, e.g. two stages contradict each other.
6. **No new content.** Do not add findings, approaches, scenarios, priorities, measures or metadata that the stage artifacts do not contain. If something looks wrong upstream, record a `synthesize-and-review` gap describing it instead of silently fixing it.

## Rules

- The report is a faithful projection. If the report and a stage artifact disagree, the report is wrong.
- **Correct:** a risk rationale `"Shared link saturates when all units report (evidence: AE-4, AE-7; basis: inferred)"`.
- **Incorrect:** adding `"evidence_ids": ["AE-4"]` as a key inside a risk. The contract forbids it, and the report would fail validation.

## Expected Output

Write `/artifacts/05_atam_report.json` conforming to `/agent/skills/synthesize-report/references/atam-report.schema.json`:

```json
{
  "ATAM_Evaluation": {
    "title": "string",
    "metadata": {"system_name": null, "date": null, "ref": null, "evaluator_organization": null,
                 "phase_1_attendees": [], "phase_2_attendees": []},
    "evaluation_inputs": {"...": "exact copy of 00_evaluation_inputs.json.evaluation_inputs"},
    "evaluation_results": {
      "utility_tree": {"root": "Utility", "quality_attribute_nodes": [
        {"attribute_name": "string", "children": [
          {"refinement": "string", "scenario_id": "RS-01", "scenario_description": "string",
           "priority_tuple": {"importance": "High", "difficulty": "Medium"}}]}]},
      "architectural_approaches": [
        {"approach_name": "string", "description": "string (evidence: AE-1)",
         "addressed_attributes": [{"quality_attribute": "string", "rationale": "string"}]}],
      "analysis_records": [
        {"scenario_reference": {"id": "RS-01", "text": "string", "type": "utility-tree"},
         "quality_attribute": "string", "environment": "string", "stimulus": "string", "response_measure": "string",
         "architectural_decisions": ["string"], "reasoning": "string (approaches: AP-1; evidence: AE-2)",
         "findings": {
           "risks": [{"id": "R-1", "description": "string", "rationale": "string (evidence: AE-2; basis: inferred)"}],
           "non_risks": [{"id": "NR-1", "description": "string", "rationale": "string (evidence: AP-1; basis: observed)"}],
           "sensitivity_points": [{"id": "S-1", "parameter": "string (evidence: AE-4)", "correlated_attribute": "string"}],
           "tradeoff_points": [{"id": "T-1", "parameter": "string (evidence: AE-4)", "conflicting_attributes": ["string", "string"]}]}}],
      "scenarios": [{"scenario_text": "string", "primary_quality_attribute": ["string"]}],
      "semantic_state": {
        "context_status": {"value": "missing | partial | sufficient", "evidence": ["string"]},
        "driver_status": {"value": "missing | partial | sufficient", "evidence": ["string"]},
        "architecture_evidence_status": {"value": "missing | partial | sufficient", "evidence": ["string"]},
        "scenario_analysis_status": {"value": "not_started | partial", "evidence": ["string"]},
        "report_status": {"value": "draft", "evidence": ["string"]},
        "gaps": [{"description": "[unknown] string (G-1-1)", "affected_activity": "establish-context",
                  "missing_evidence": "string", "resolution_question": "string"}]
      }
    }
  }
}
```

Read the file back and verify that it parses, that it has no keys beyond the contract, that `evaluation_inputs` equals the input, that the record and finding counts equal `04_analysis.json`, and that every stage gap id appears in a report gap description.

Do not review the report or decide readiness; the check-evaluation task does that.
