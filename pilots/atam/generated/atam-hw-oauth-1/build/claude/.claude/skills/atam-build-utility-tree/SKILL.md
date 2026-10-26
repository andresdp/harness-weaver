---
name: atam-build-utility-tree
description: "ATAM stage 2 (build-utility-tree): refines quality attribute drivers and raw candidate scenarios into a utility tree of measurable scenarios (stimulus, environment, response, response measure), assigns priority tuples only where evidence supports them, fixes the analysis order, and writes 02_utility_tree.json. Used by the atam-utility-tree-analyst agent inside the atam-evaluation pipeline, including re-runs of this stage; for a whole evaluation use atam-evaluation."
---

# Build the Utility Tree (ATAM activity `build-utility-tree`)

## Objective

Turn the quality attribute drivers into concrete, analyzable scenarios grouped under a `Utility` root, prioritizing them only as far as the evidence allows. Unsupported priorities and measures stay explicitly unresolved. Method basis: step 2 of `.claude/skills/evaluate-architecture/SKILL.md`. Methodology profile: `.claude/skills/atam-build-utility-tree/references/methodology.yaml`.

## Input Artifacts

Read: `_workspace/00_evaluation_inputs.json` (for `raw_candidate_scenarios` and cited values) and `_workspace/01_context.json` (business drivers `BD-n`, architecture evidence `AE-n`, gaps).

## Evidence conventions (shared by every ATAM stage)

- **Allowed sources.** Use only `_workspace/00_evaluation_inputs.json` and the upstream artifacts listed under Input Artifacts. Never read or request reference evaluation outputs (`ground_truth_outputs`) or any earlier evaluation of the same system. They are evaluator-only.
- **`source_refs`** are JSON paths into `00_evaluation_inputs.json`. They start at `evaluation_inputs`, `metadata` or `title` and use the exact keys present, for example `evaluation_inputs.business_context.business_goals[0]` or `evaluation_inputs.quantitative_model_parameters["network bandwidth"]`. Before writing a path, confirm it exists in the input.
- **`basis`**: `observed` means the input states it (cite at least one `source_ref`). `inferred` means it is reasoned from cited inputs (cite them and state the reasoning). `assumption` means the inputs do not support it, so it must also be recorded as a gap of type `assumption`. Never present an inference or an assumption as observed.
- **IDs** are stable within a run and are how artifacts link: `BD-n` business drivers, `AE-n` architecture evidence, `Q-n` open questions, scenario ids, `AP-n` approaches, `AR-n` analysis records, `R-n`/`NR-n`/`S-n`/`T-n` findings and `G-<stage>-<n>` gaps. Link by ID, never by paraphrase.
- **Gaps** record what is unknown, conflicting, incomplete or assumed: `{"id": "G-<stage>-<n>", "gap_type": "unknown|conflict|incomplete|assumption", "description": "...", "affected_activity": "<activity id>", "missing_evidence": "...", "resolution_question": "..."}`. Activity ids: `establish-context`, `build-utility-tree`, `identify-approaches`, `analyze-scenarios`, `synthesize-and-review`. A gap is a finding, not a failure. Missing evidence never licenses invention.
- **Status evidence** names observed facts about the inputs or artifacts, including absences, for example `"evaluation_inputs has no phase_2_architectural_context key"` or `"evaluation_inputs.raw_candidate_scenarios has 6 entries; 2 state a measurable response"`. Agent activity ("task completed", "stage ran") is never evidence of methodology progress.

## Procedure

1. **Readiness.** If `01_context.json` has `driver_status` = `missing`, build what the raw candidate scenarios allow, record a gap that the drivers are missing, and continue. Never invent drivers.
2. **Quality attribute nodes.** Create one node per quality attribute named in `BD-n` items of kind `architectural_driver`, plus any attribute a raw candidate scenario clearly exercises. Use the input's attribute names; if you normalize a name (e.g. "speed" → "Performance"), keep the original in `refinement`. List the supporting `BD` ids in `driver_ids`.
3. **Refine raw candidate scenarios.** For every entry in `evaluation_inputs.raw_candidate_scenarios`:
   - attach it to the attribute it primarily exercises; reuse its `id` as `scenario_id` (e.g. `RS-03`), and set `origin` = `raw_candidate_scenario` and `raw_scenario_id` = that id;
   - split it into `stimulus`, `environment` and `response`, worded from the raw text; `scenario_description` is one sentence combining them;
   - `refinement` names the concern being refined (e.g. "Latency of periodic position updates").
   If a raw scenario cannot be refined (too vague, or no attribute applies), leave it out of the tree and record a gap naming its id and the reason.
4. **Driver-derived scenarios (sparingly).** When an `architectural_driver` has no raw scenario at all, you may add at most one scenario for it, with `origin` = `derived_from_driver`, an id such as `UT-<ATTR>-1`, `source_refs` citing the driver, and a gap of type `assumption` asking the architect to confirm the scenario. Never derive scenarios for attributes the inputs do not mention.
5. **Response measures.** Set `response_measure` only from a stated requirement, a quantitative parameter or a runtime constraint in the input (`response_measure_basis` = `observed`), or from an explicit calculation over cited values (`inferred`; show the calculation in the text). Otherwise set `null` with `response_measure_basis` = `missing` and record a gap. Never pick a "typical" threshold.
6. **Priority tuples** (`importance`, `difficulty` ∈ High/Medium/Low). Assign one only when the input supports both values, e.g. explicitly ranked business goals for importance plus evidence of architectural difficulty such as a stated hard constraint. Write the cited evidence in `priority_basis`. Otherwise set `priority_tuple` and `priority_basis` to `null` and record one gap stating that stakeholder prioritization is unavailable for the listed scenario ids.
7. **`scenarios`**: one entry per tree scenario: `scenario_id`, `scenario_text` (= its `scenario_description`, verbatim) and `primary_quality_attribute` (one or more attributes).
8. **`analysis_order`**: every scenario id exactly once. With priorities, order (High, High) first, then (High, Medium), (Medium, High) and so on down the tuples. Without priorities, keep input order (raw scenarios first, then derived ones), and say so in the prioritization gap.
9. **`driver_status`**: re-assess the `01_context.json` value now that scenarios exist (e.g. `partial` when drivers exist but no scenario has a response measure). Cite counts as evidence.

## Rules

- Keep the raw scenario's meaning: refine it, never strengthen it. Do not add load levels, failure modes or numbers the raw text and inputs do not give.
- **Correct:** raw "System must handle peak load" + no stated peak in the input → `"response_measure": null, "response_measure_basis": "missing"` and gap "Peak load level and acceptable response for RS-02 are not stated".
- **Incorrect:** `"response_measure": "95th percentile latency < 200 ms at 10,000 users"` when no such figure appears in the input.

## Expected Output

Write `_workspace/02_utility_tree.json` conforming to `.claude/skills/atam-build-utility-tree/references/utility-tree.schema.json`:

```json
{
  "root": "Utility",
  "quality_attribute_nodes": [
    {"attribute_name": "string", "driver_ids": ["BD-1"],
     "children": [
       {"scenario_id": "RS-01", "refinement": "string", "scenario_description": "string",
        "stimulus": "string", "environment": "string", "response": "string",
        "response_measure": "string or null", "response_measure_basis": "observed | inferred | missing",
        "priority_tuple": {"importance": "High | Medium | Low", "difficulty": "High | Medium | Low"},
        "priority_basis": "string or null (null exactly when priority_tuple is null)",
        "origin": "raw_candidate_scenario | derived_from_driver", "raw_scenario_id": "RS-01 or null",
        "source_refs": ["evaluation_inputs.raw_candidate_scenarios[0]"]}
     ]}
  ],
  "scenarios": [{"scenario_id": "RS-01", "scenario_text": "string", "primary_quality_attribute": ["string"]}],
  "analysis_order": ["RS-01"],
  "driver_status": {"value": "missing | partial | sufficient", "evidence": ["string"]},
  "gaps": [
    {"id": "G-2-1", "gap_type": "unknown | conflict | incomplete | assumption", "description": "string",
     "affected_activity": "build-utility-tree", "missing_evidence": "string", "resolution_question": "string"}
  ]
}
```

Read the file back and verify that it parses, that every `driver_ids` entry exists in `01_context.json`, that `analysis_order` lists every scenario id exactly once, and that every null measure or priority is covered by a `build-utility-tree` gap.

The orchestrator also runs `validate_artifacts.py check _workspace --stage 3` once stage 3 has finished too. Fix any failure it attributes to `02_utility_tree.json`.

Do not identify architectural approaches or analyze scenarios; later stages do that.
