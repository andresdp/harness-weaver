---
name: establish-context
description: "ATAM stage 1 (establish-context): extracts system scope, business drivers, architecture evidence, metadata and open questions from the supplied evaluation inputs, assesses context/driver/architecture-evidence availability with evidence, records gaps, and writes 01_context.json."
---

# Establish Context (ATAM activity `establish-context`)

## Objective

Turn the supplied evaluation inputs into a traceable inventory: what the system is, which business drivers and constraints apply, what architecture evidence exists, and what remains open. Later stages may use only what this inventory records and cites. Method basis: step 1 of `/agent/skills/establish-context/references/evaluate-architecture.md`. Methodology profile: `/agent/skills/establish-context/references/methodology.yaml`.

## Input Artifacts

Read: `/artifacts/00_evaluation_inputs.json` (input port `evaluation_inputs`).

If the file wraps its content in `ATAM_Evaluation`, treat `ATAM_Evaluation.evaluation_inputs` as `evaluation_inputs`, and write `source_refs` relative to that object (starting at `evaluation_inputs`).

## Evidence conventions (shared by every ATAM stage)

- **Allowed sources.** Use only `/artifacts/00_evaluation_inputs.json` and the upstream artifacts listed under Input Artifacts. Never read or request reference evaluation outputs (`ground_truth_outputs`) or any earlier evaluation of the same system. They are evaluator-only.
- **`source_refs`** are JSON paths into `00_evaluation_inputs.json`. They start at `evaluation_inputs`, `metadata` or `title` and use the exact keys present, for example `evaluation_inputs.business_context.business_goals[0]` or `evaluation_inputs.quantitative_model_parameters["network bandwidth"]`. Before writing a path, confirm it exists in the input.
- **`basis`**: `observed` means the input states it (cite at least one `source_ref`). `inferred` means it is reasoned from cited inputs (cite them and state the reasoning). `assumption` means the inputs do not support it, so it must also be recorded as a gap of type `assumption`. Never present an inference or an assumption as observed.
- **IDs** are stable within a run and are how artifacts link: `BD-n` business drivers, `AE-n` architecture evidence, `Q-n` open questions, scenario ids, `AP-n` approaches, `AR-n` analysis records, `R-n`/`NR-n`/`S-n`/`T-n` findings and `G-<stage>-<n>` gaps. Link by ID, never by paraphrase.
- **Gaps** record what is unknown, conflicting, incomplete or assumed: `{"id": "G-<stage>-<n>", "gap_type": "unknown|conflict|incomplete|assumption", "description": "...", "affected_activity": "<activity id>", "missing_evidence": "...", "resolution_question": "..."}`. Activity ids: `establish-context`, `build-utility-tree`, `identify-approaches`, `analyze-scenarios`, `synthesize-and-review`. A gap is a finding, not a failure. Missing evidence never licenses invention.
- **Status evidence** names observed facts about the inputs or artifacts, including absences, for example `"evaluation_inputs has no phase_2_architectural_context key"` or `"evaluation_inputs.raw_candidate_scenarios has 6 entries; 2 state a measurable response"`. Agent activity ("task completed", "stage ran") is never evidence of methodology progress.

## Procedure

1. **Check the reference boundary first.** Search the whole input for the keys `ground_truth_outputs` and `evaluation_results`. If either is present, STOP: write no artifact, and report "Input rejected: it contains evaluator-only reference outputs; supply an input-only copy." The evaluation must never see reference answers.
2. **Inventory the input.** List every key under `evaluation_inputs`, including nested ones. ArchEval-shaped inputs usually contain the keys below. Map each element you find; map any other key by its meaning; never drop an element silently.

   | Input element | Goes to |
   |---|---|
   | `system_description` | `system_scope.summary` (condensed, observed) and atomic `AE-n` items of kind `system_description` for each architectural statement it makes |
   | `business_context.business_goals[]` | `BD-n`, kind `business_goal` |
   | `business_context.technical_constraints[]` | `BD-n`, kind `technical_constraint` |
   | `business_context.architectural_drivers[]` | `BD-n`, kind `architectural_driver` (these are quality attribute drivers) |
   | `phase_2_architectural_context.runtime_constraints[]` | `BD-n`, kind `runtime_constraint` |
   | `phase_2_architectural_context.hardware_view_description[]` | `AE-n`, kind `deployment_topology` |
   | `quantitative_model_parameters.*` | `AE-n`, kind `quantitative_parameter`, one per parameter or group, values copied exactly with units |
   | `investigative_prompts.style_probes.target_style` | `AE-n`, kind `style_probe`: the style evaluators are probing. This is *not* proof that the system uses that style |
   | `investigative_prompts.style_probes.questions[]` | `Q-n`, origin `investigative_prompt` |
   | `phase_1_discovery.initial_documentation_status` | `AE-n`, kind `documentation_status` |
   | `phase_1_discovery.evaluator_inquiry_questions[]` | `Q-n`, origin `input_inquiry_question` |
   | `raw_candidate_scenarios[]` | not inventoried here; stage 2 refines them. Note their count in the `driver_status` evidence |

   Keep statements close to the input wording. Split compound sentences into atomic items only where each part is a separate fact.
3. **Metadata.** Fill `metadata` from the input's `metadata` object when present, mapping `system_name`, `date`, `ref`, `evaluator_organization`, `phase_1_attendees` and `phase_2_attendees` by name. Use `null` (or `[]` for attendee lists) for anything absent. A system name may come from `system_description` only if the input states it verbatim. Never invent a date, an organization or attendees.
4. **Open questions.** Add `Q-n` items of origin `evaluator_gap` only for questions an architect must answer before the evaluation can be grounded (e.g. "Which component owns retry logic?"). Each must point at a gap.
5. **Assess availability**, each with evidence:
   - `context_status`: `sufficient` when a system description, business goals and constraints are all present and specific; `partial` when some are present or they are vague; `missing` when there is neither a system description nor business context.
   - `driver_status`: `sufficient` when quality attribute drivers are named and business goals give them importance; `partial` when only one of the two is present, or drivers are named without any scenarios or measures; `missing` when no driver can be identified.
   - `architecture_evidence_status`: `sufficient` when structure or topology (components, connectors, deployment, key mechanisms) is described well enough to name approaches; `partial` for description-level statements only; `missing` when none exists.
6. **Record gaps** for every `missing` or `partial` status, every absent template element that later stages need (e.g. no quantitative parameters means response measures cannot be checked) and every conflict between input statements. Keep conflicting statements side by side as separate items; do not resolve them.

## Rules

- Record only what the input says or what you can cite. Do not add domain knowledge about "systems like this".
- A style probe or an inquiry question shows what evaluators asked, not what the architecture is.
- **Correct:** `{"id": "AE-3", "evidence_kind": "style_probe", "statement": "Evaluators probe the publish-subscribe style.", "basis": "observed", "source_refs": ["evaluation_inputs.investigative_prompts.style_probes.target_style"]}`
- **Incorrect:** `{"id": "AE-3", "evidence_kind": "structure", "statement": "The system uses publish-subscribe.", "basis": "observed", ...}`. The input never states the system uses it.

## Expected Output

Write `/artifacts/01_context.json` conforming to `/agent/skills/establish-context/references/context.schema.json`:

```json
{
  "metadata": {"system_name": null, "date": null, "ref": null, "evaluator_organization": null,
               "phase_1_attendees": [], "phase_2_attendees": []},
  "system_scope": {"summary": "string", "basis": "observed", "source_refs": ["evaluation_inputs.system_description"]},
  "business_drivers": [
    {"id": "BD-1", "kind": "business_goal | technical_constraint | architectural_driver | runtime_constraint | other",
     "statement": "string", "basis": "observed | inferred | assumption", "source_refs": ["evaluation_inputs.business_context.business_goals[0]"]}
  ],
  "architecture_evidence": [
    {"id": "AE-1", "evidence_kind": "system_description | structure | deployment_topology | runtime_constraint | quantitative_parameter | style_probe | documentation_status | other",
     "statement": "string", "basis": "observed | inferred | assumption", "source_refs": ["evaluation_inputs.system_description"]}
  ],
  "open_questions": [
    {"id": "Q-1", "question": "string", "origin": "input_inquiry_question | investigative_prompt | evaluator_gap",
     "source_refs": ["evaluation_inputs.phase_1_discovery.evaluator_inquiry_questions[0]"]}
  ],
  "context_status": {"value": "missing | partial | sufficient", "evidence": ["string"]},
  "driver_status": {"value": "missing | partial | sufficient", "evidence": ["string"]},
  "architecture_evidence_status": {"value": "missing | partial | sufficient", "evidence": ["string"]},
  "gaps": [
    {"id": "G-1-1", "gap_type": "unknown | conflict | incomplete | assumption", "description": "string",
     "affected_activity": "establish-context", "missing_evidence": "string", "resolution_question": "string"}
  ]
}
```

Read the file back and verify that it exists, parses as JSON, uses only the keys above, and that every `source_ref` resolves in `00_evaluation_inputs.json`.

Do not build the utility tree, name architectural approaches or judge risks; later stages do that.
