---
name: identify-approaches
description: "ATAM stage 3 (identify-approaches): identifies the architectural approaches (styles, patterns, tactics, key decisions) that the supplied architecture evidence shows or implies, separates observed decisions from inferred approaches, links each to AE evidence ids and the quality attributes it addresses, and writes 03_approaches.json."
---

# Identify Architectural Approaches (ATAM activity `identify-approaches`)

## Objective

Name the architectural approaches the evaluated architecture actually uses, as far as the supplied evidence shows, so that scenarios can be analyzed against concrete decisions. Method basis: step 3 of `/agent/skills/identify-approaches/references/evaluate-architecture.md`. Methodology profile: `/agent/skills/identify-approaches/references/methodology.yaml`.

## Input Artifacts

Read: `/artifacts/00_evaluation_inputs.json` (to check wording) and `/artifacts/01_context.json` (architecture evidence `AE-n`, drivers `BD-n`, gaps). This stage does not need the utility tree.

## Evidence conventions (shared by every ATAM stage)

- **Allowed sources.** Use only `/artifacts/00_evaluation_inputs.json` and the upstream artifacts listed under Input Artifacts. Never read or request reference evaluation outputs (`ground_truth_outputs`) or any earlier evaluation of the same system. They are evaluator-only.
- **`source_refs`** are JSON paths into `00_evaluation_inputs.json`. They start at `evaluation_inputs`, `metadata` or `title` and use the exact keys present, for example `evaluation_inputs.business_context.business_goals[0]` or `evaluation_inputs.quantitative_model_parameters["network bandwidth"]`. Before writing a path, confirm it exists in the input.
- **`basis`**: `observed` means the input states it (cite at least one `source_ref`). `inferred` means it is reasoned from cited inputs (cite them and state the reasoning). `assumption` means the inputs do not support it, so it must also be recorded as a gap of type `assumption`. Never present an inference or an assumption as observed.
- **IDs** are stable within a run and are how artifacts link: `BD-n` business drivers, `AE-n` architecture evidence, `Q-n` open questions, scenario ids, `AP-n` approaches, `AR-n` analysis records, `R-n`/`NR-n`/`S-n`/`T-n` findings and `G-<stage>-<n>` gaps. Link by ID, never by paraphrase.
- **Gaps** record what is unknown, conflicting, incomplete or assumed: `{"id": "G-<stage>-<n>", "gap_type": "unknown|conflict|incomplete|assumption", "description": "...", "affected_activity": "<activity id>", "missing_evidence": "...", "resolution_question": "..."}`. Activity ids: `establish-context`, `build-utility-tree`, `identify-approaches`, `analyze-scenarios`, `synthesize-and-review`. A gap is a finding, not a failure. Missing evidence never licenses invention.
- **Status evidence** names observed facts about the inputs or artifacts, including absences, for example `"evaluation_inputs has no phase_2_architectural_context key"` or `"evaluation_inputs.raw_candidate_scenarios has 6 entries; 2 state a measurable response"`. Agent activity ("task completed", "stage ran") is never evidence of methodology progress.

## Procedure

1. **Readiness.** If `architecture_evidence_status` in `01_context.json` is `missing`, write an empty `approaches` list, set `architecture_evidence_status` to `missing` with evidence, record a gap ("No architecture evidence to identify approaches"), and stop.
2. **Collect candidate approaches** from `AE-n` items of kind `system_description`, `structure`, `deployment_topology`, `runtime_constraint` and `quantitative_parameter`: architectural styles (e.g. layered, client-server, publish-subscribe), patterns, tactics (e.g. caching, replication, heartbeat) and other system-wide decisions (e.g. a single central database, a bandwidth-limited link).
3. **Classify the basis.**
   - `observed`: the evidence names the approach or describes its mechanism unambiguously (e.g. "clients subscribe to topics on a broker").
   - `inferred`: the evidence implies the approach without naming it. Write `inference_note` stating which statements imply it and what would confirm it, and record a gap of type `unknown` asking the architect to confirm.
   - A `style_probe` item alone never makes an approach `observed`. It can support an inferred approach only together with other evidence; otherwise record the probed style as an open gap ("Is <style> used, and where?").
4. **Describe each approach** as the evidence describes its application in *this* system (`description`), not the textbook definition. Cite `evidence_ids` (at least one `AE` id).
5. **Addressed attributes.** For each approach, list the quality attributes it is intended to support, with a `rationale` tying the mechanism to the attribute. Prefer attributes named in the drivers (`BD-n`). Record negative effects for stage 4 to analyze as a tradeoff or risk, not here.
6. **`architecture_evidence_status`**: re-assess the `01_context.json` value now that you know whether the evidence was enough to name approaches. Cite the observed/inferred counts as evidence.
7. **Gaps** for every inferred approach, every probed but unconfirmed style, and every major element (e.g. persistence, communication, deployment) the evidence leaves undescribed.

## Rules

- One approach per distinct decision; do not split a style into its textbook sub-patterns unless the evidence shows each.
- **Correct:** evidence "All stations exchange updates through the central server" → `{"approach_name": "Centralized client-server communication", "basis": "observed", "evidence_ids": ["AE-2"], ...}`.
- **Incorrect:** adding "Microservices with an API gateway" because the system is web-based, with no supporting evidence item.

## Expected Output

Write `/artifacts/03_approaches.json` conforming to `/agent/skills/identify-approaches/references/approaches.schema.json`:

```json
{
  "approaches": [
    {"id": "AP-1", "approach_name": "string", "description": "string",
     "basis": "observed | inferred", "inference_note": "string or null (required when inferred)",
     "evidence_ids": ["AE-1"],
     "addressed_attributes": [{"quality_attribute": "string", "rationale": "string"}]}
  ],
  "architecture_evidence_status": {"value": "missing | partial | sufficient", "evidence": ["string"]},
  "gaps": [
    {"id": "G-3-1", "gap_type": "unknown | conflict | incomplete | assumption", "description": "string",
     "affected_activity": "identify-approaches", "missing_evidence": "string", "resolution_question": "string"}
  ]
}
```

Read the file back and verify that it parses, that every `evidence_ids` entry exists in `01_context.json`, and that every inferred approach has an `inference_note` and a gap.

Do not analyze scenarios or report risks, sensitivity points or tradeoffs; stage 4 does that.
