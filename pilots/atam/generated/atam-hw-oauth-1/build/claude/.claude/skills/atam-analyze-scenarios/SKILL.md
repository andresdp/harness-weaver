---
name: atam-analyze-scenarios
description: "ATAM stage 4 (analyze-scenarios): analyzes each utility-tree scenario, in analysis order, against the identified architectural approaches and records architectural decisions, reasoning, risks, non-risks, sensitivity points and tradeoff points with evidence ids, then writes 04_analysis.json. Used by the atam-scenario-analyst agent inside the atam-evaluation pipeline, including re-runs of this stage; for a whole evaluation use atam-evaluation."
---

# Analyze Scenarios (ATAM activity `analyze-scenarios`)

## Objective

For each prioritized scenario, determine how the architectural approaches affect the scenario's response, and record the ATAM findings that the evidence supports. Method basis: step 4 of `.claude/skills/evaluate-architecture/SKILL.md`. Methodology profile: `.claude/skills/atam-analyze-scenarios/references/methodology.yaml`.

## Input Artifacts

Read: `_workspace/00_evaluation_inputs.json` (cited values), `_workspace/01_context.json` (`AE-n`, `BD-n`), `_workspace/02_utility_tree.json` (scenarios, `analysis_order`) and `_workspace/03_approaches.json` (`AP-n`).

## Evidence conventions (shared by every ATAM stage)

- **Allowed sources.** Use only `_workspace/00_evaluation_inputs.json` and the upstream artifacts listed under Input Artifacts. Never read or request reference evaluation outputs (`ground_truth_outputs`) or any earlier evaluation of the same system. They are evaluator-only.
- **`source_refs`** are JSON paths into `00_evaluation_inputs.json`. They start at `evaluation_inputs`, `metadata` or `title` and use the exact keys present, for example `evaluation_inputs.business_context.business_goals[0]` or `evaluation_inputs.quantitative_model_parameters["network bandwidth"]`. Before writing a path, confirm it exists in the input.
- **`basis`**: `observed` means the input states it (cite at least one `source_ref`). `inferred` means it is reasoned from cited inputs (cite them and state the reasoning). `assumption` means the inputs do not support it, so it must also be recorded as a gap of type `assumption`. Never present an inference or an assumption as observed.
- **IDs** are stable within a run and are how artifacts link: `BD-n` business drivers, `AE-n` architecture evidence, `Q-n` open questions, scenario ids, `AP-n` approaches, `AR-n` analysis records, `R-n`/`NR-n`/`S-n`/`T-n` findings and `G-<stage>-<n>` gaps. Link by ID, never by paraphrase.
- **Gaps** record what is unknown, conflicting, incomplete or assumed: `{"id": "G-<stage>-<n>", "gap_type": "unknown|conflict|incomplete|assumption", "description": "...", "affected_activity": "<activity id>", "missing_evidence": "...", "resolution_question": "..."}`. Activity ids: `establish-context`, `build-utility-tree`, `identify-approaches`, `analyze-scenarios`, `synthesize-and-review`. A gap is a finding, not a failure. Missing evidence never licenses invention.
- **Status evidence** names observed facts about the inputs or artifacts, including absences, for example `"evaluation_inputs has no phase_2_architectural_context key"` or `"evaluation_inputs.raw_candidate_scenarios has 6 entries; 2 state a measurable response"`. Agent activity ("task completed", "stage ran") is never evidence of methodology progress.

## ATAM finding definitions

- **Risk** (`R-n`): an architectural decision, or the absence of one, that may prevent the scenario's response or a business goal from being achieved, given the evidence.
- **Non-risk** (`NR-n`): a decision that the evidence shows is adequate for the scenario, with the reason it is safe.
- **Sensitivity point** (`S-n`): a property of one or more components or connections (a parameter) whose value strongly affects the response for one quality attribute, e.g. a buffer size, update rate or link bandwidth.
- **Tradeoff point** (`T-n`): a parameter that is a sensitivity point for two or more attributes with opposing effects, e.g. encryption strength improves security and costs latency.

## Procedure

1. **Readiness.** Stop with a gap if `02_utility_tree.json` has no scenarios. If `03_approaches.json` has no approaches, list every scenario under `unanalyzed_scenarios` with the reason "no architecture approaches identified", set `scenario_analysis_status` to `not_started` with evidence, and finish.
2. **Work in `analysis_order`.** For each scenario id:
   a. Copy `quality_attribute` (its node's attribute), `environment` and `stimulus` from the tree. Copy `response_measure` when present; otherwise write `"unspecified (see gap G-2-n)"` with the actual gap id.
   b. `scenario_reference`: `id` = the scenario id; `text` = the scenario's `scenario_description` copied **verbatim**; `type` = `utility-tree` (or `raw-candidate` when the tree reused a raw id and you quote the raw text instead).
   c. Select the approaches (`approach_ids`) and evidence (`evidence_ids`) that bear on this scenario. `architectural_decisions` restates those decisions as they apply here.
   d. `reasoning`: connect the decisions to the response step by step. When quantitative parameters allow it (e.g. message size × rate vs. bandwidth), do the arithmetic with the cited values and show it, marking the conclusion `inferred`.
   e. Record findings only where the reasoning and evidence support them. Each finding has `basis` (`observed` when the input itself states the problem or safety; otherwise `inferred`) and `evidence_ids` (AE/AP/BD/scenario ids or input paths). Number `R-`, `NR-`, `S-` and `T-` ids sequentially across the whole artifact, not per record.
   f. If the scenario cannot be analyzed because no approach bears on it or the decisive evidence is missing, add it to `unanalyzed_scenarios` with the reason and record a gap. Never fill the hole with generic risks.
3. **`scenario_analysis_status`**: `partial` when at least one scenario was analyzed; `not_started` when none was. Evidence names the counts (e.g. "AR-1..AR-5 analyze 5 of 6 scenarios in analysis_order; RS-04 unanalyzed, see G-4-1"). This harness never sets `reviewed`; only a recorded architect review can.
4. **Gaps** for each unanalyzed scenario, each finding that depends on an unconfirmed (inferred) approach, and each place where a missing response measure prevents judging whether the response is met.

## Rules

- A finding must name the specific decision or parameter involved. "Performance may be a concern" is not a finding.
- Absence of evidence is a gap, not a risk. Record a risk for a missing mechanism only when the scenario makes that mechanism necessary (e.g. a failover scenario with no stated redundancy). State that reasoning and mark it `inferred`.
- **Correct:** `{"id": "S-2", "parameter": "Position update rate (cited: 1 Hz per unit, AE-6)", "correlated_attribute": "Performance", "evidence_ids": ["AE-6"]}`
- **Incorrect:** `{"id": "R-7", "description": "The system may not scale", "rationale": "Scalability is often an issue", ...}`. No decision named, no evidence.

## Expected Output

Write `_workspace/04_analysis.json` conforming to `.claude/skills/atam-analyze-scenarios/references/analysis.schema.json`:

```json
{
  "analysis_records": [
    {"record_id": "AR-1", "scenario_id": "RS-01", "approach_ids": ["AP-1"], "evidence_ids": ["AE-2"],
     "scenario_reference": {"id": "RS-01", "text": "verbatim scenario_description", "type": "utility-tree"},
     "quality_attribute": "string", "environment": "string", "stimulus": "string", "response_measure": "string",
     "architectural_decisions": ["string"], "reasoning": "string",
     "findings": {
       "risks": [{"id": "R-1", "description": "string", "rationale": "string", "basis": "observed | inferred", "evidence_ids": ["AE-2"]}],
       "non_risks": [{"id": "NR-1", "description": "string", "rationale": "string", "basis": "observed | inferred", "evidence_ids": ["AP-1"]}],
       "sensitivity_points": [{"id": "S-1", "parameter": "string", "correlated_attribute": "string", "evidence_ids": ["AE-4"]}],
       "tradeoff_points": [{"id": "T-1", "parameter": "string", "conflicting_attributes": ["Attribute A (+)", "Attribute B (-)"], "evidence_ids": ["AE-4"]}]
     }}
  ],
  "unanalyzed_scenarios": [{"scenario_id": "RS-04", "reason": "string"}],
  "scenario_analysis_status": {"value": "not_started | partial", "evidence": ["string"]},
  "gaps": [
    {"id": "G-4-1", "gap_type": "unknown | conflict | incomplete | assumption", "description": "string",
     "affected_activity": "analyze-scenarios", "missing_evidence": "string", "resolution_question": "string"}
  ]
}
```

Read the file back and verify that it parses, that every id in `analysis_order` appears in exactly one record or in `unanalyzed_scenarios`, that each `scenario_reference.text` matches the tree verbatim, and that every `approach_ids`/`evidence_ids` entry exists upstream.

The orchestrator also runs `validate_artifacts.py check _workspace --stage 4`. Fix exactly the failures it reports.

Do not assemble the final report; stage 5 does that.
