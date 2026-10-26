# Stage artifacts 00–05: what each stage writes and how it is gated

Read the section for your stage. Every artifact lives in `_workspace/`. Its JSON Schema is the normative shape:
`atam_harness/schemas/0N_*.schema.json` for 01–03, and `analysis.schema.json` (next to this file) for 04.
Run `python3 atam_harness/atam.py validate <stage-id>` until it prints no errors. That command is the same gate
the runner applies; if it fails, the stage fails.

## Contents
1. Identifier namespaces
2. Basis: observed, inferred, assumption
3. 00_evaluation_inputs.json (stage0-intake, deterministic)
4. 01_context.json (stage1-establish_context)
5. 02_utility_tree.json (stage2-build_utility_tree)
6. 03_approaches.json (stage3-identify_approaches)
7. 04_analysis.json (stage4-analyze_scenarios)
8. 05_atam_report_draft.json (stage5-synthesize_report)
9. Phrasing patterns

## 1. Identifier namespaces

| Prefix | Meaning | Registered in | May be cited as evidence |
| --- | --- | --- | --- |
| `AE-n` | Architecture evidence: one observed statement from the inputs | 01 `architecture_evidence` | yes, everywhere evidence is allowed |
| `BD-n` | Business driver or constraint: one observed statement | 01 `business_drivers` | only in risk / non-risk `evidence_ids` |
| `AP-n` | Architectural approach | 03 `approaches` | only in risk / non-risk `evidence_ids` and record `approach_ids` |
| `G-<stage>-n` | Gap: unknown, conflict, incomplete input or assumption | the `gaps` array of the stage that found it | **never** |
| `AR-n`, `R-n`, `NR-n`, `S-n`, `T-n` | Analysis record and finding ids | 04 | they are ids, not evidence |

Gap ids appear **only** inside gap records. This applies to every other string as well: reasoning, rationale,
response_measure, decision text, descriptions. `analysis.schema.json` suggests writing a response measure as
`unspecified (see gap G-x-y)`. This harness does not allow that: write `unspecified: no response measure supplied`
and keep the gap in `gaps`. The projection makes every gap visible in the report, and the stage-4 gate rejects any
`G-*` id found outside `gaps`.

Finding ids (`R-n`, `NR-n`, `S-n`, `T-n`) are unique across the whole 04 artifact, not per record.

## 2. Basis

- **observed**: the inputs (or a validated upstream artifact) state the claim directly. AE/BD items are always
  observed and carry `source_refs` that resolve inside `00_evaluation_inputs.json`.
- **inferred**: you reasoned from evidence to the claim. That includes every conclusion drawn from something
  *not* being described. A premise can be observed while the conclusion drawn from it is still inferred.
- **assumption**: no supplied evidence supports the claim. Do not use it as a finding. Record it as a gap
  with `gap_type: assumption`.

Absence can establish uncertainty ("the supplied material does not establish X"). It cannot establish that X
is false, missing in the real system, or violated.

## 3. 00_evaluation_inputs.json

`atam.py intake` writes this file from the user's template-shaped JSON. Its top-level keys are `title`
(optional), `metadata` (optional) and `evaluation_inputs`. Intake refuses input that contains
`ground_truth_outputs` or any other top-level section. Every `source_refs` path starts at this object, for
example `evaluation_inputs.business_context.business_goals[0]`. Keys containing `.`, `[` or `]` use bracket
form: `evaluation_inputs.quantitative_model_parameters["msg.size"]`.

## 4. 01_context.json (activity establish-context)

- `system_scope`: a short summary of what the inputs say the system is, with refs.
- `business_drivers` (`BD-n`): business goals, business and technical constraints, and named architectural
  drivers, one statement per item, copied or tightly paraphrased.
- `architecture_evidence` (`AE-n`): one atomic architecture fact per item, such as a component, connector,
  deployment or hardware statement, a runtime constraint, a quantitative parameter (keep its value and unit),
  a style probe, or the documentation status. Do not merge two facts into one AE, because later findings cite AE ids
  individually.
- `open_questions`: questions the inputs themselves raise (for example `evaluator_inquiry_questions`), with refs.
- `context_status`, `driver_status`, `architecture_evidence_status`: `missing | partial | sufficient`, each
  with at least one evidence string naming what is present or absent (for example "No hardware view is supplied").
  Use `sufficient` only when nothing material for that status is missing.
- `gaps` (`G-1-n`): missing context, stakeholder priorities, conflicting statements.

## 5. 02_utility_tree.json (activity build-utility-tree)

- One `quality_attribute_nodes` entry per quality attribute that the drivers or scenarios support.
- Each child scenario has `stimulus`, `environment`, `response` and a `scenario_description` sentence that
  combines them. Stage 4 copies the `scenario_description` verbatim into `scenario_reference.text`.
- `origin`: either `raw_candidate_scenario` (with its `RS-xx` id) or a scenario derived from drivers or
  evidence (basis `inferred`). Every origin carries refs.
- `response_measure`: set `value` only when the inputs state a measure, with basis `observed` and refs.
  Otherwise use `value: null` and basis `unspecified`, and add a G-2-n gap whose description names the
  scenario id. Never fabricate a threshold.
- `priority_tuple`: give it only when the inputs state importance and difficulty (basis `observed` with refs).
  Otherwise use `null`, and record the missing priority as a gap. Never rank scenarios on stakeholders' behalf.
- Ids: a letter followed by letters, digits, `_`, `.` or `-` (for example `P1`, `AV-2`). They must be unique.

## 6. 03_approaches.json (activity identify-approaches)

- An approach the inputs name is `observed`. An approach you recognise from the evidence (for example "the
  description of a broker implies publish-subscribe") is `inferred` and needs an `inference_note` explaining the
  step. Every approach cites `AE-n` ids.
- `addressed_attributes` rationales explain how the approach helps or hinders the attribute. They have their
  own basis and evidence. Don't add an evidence suffix yourself; the projection adds it.

## 7. 04_analysis.json (activity analyze-scenarios), governed by analysis.schema.json

- Give every utility-tree scenario an analysis record, or list it in `unanalyzed_scenarios` with a reason
  (and normally a gap).
- `scenario_reference`: `id` is the scenario_id, `text` is the verbatim `scenario_description`, `type` is the
  scenario's `scenario_type`.
- `response_measure`: copy the utility-tree value exactly, or write `unspecified: ...` with no gap id.
- `architectural_decisions`: one string per decision, each ending with `(evidence: AE-n[, AE-m])`.
- `reasoning`: connect the decisions to the response. For a scenario without a measure, say that attainment
  cannot be determined.
- Risks and non-risks: `description` states the concern, and `rationale` gives the reasoning. Set `basis` per
  §2. `evidence_ids` may use AE, AP or BD ids, and needs at least one. Don't append the suffix yourself.
- Sensitivity points and tradeoff points: the `parameter` names the architectural parameter, and
  `evidence_ids` are AE only. A tradeoff names at least two conflicting attributes.
- `scenario_analysis_status`: `not_started` or `partial`. The harness never sets `reviewed`.
- `gaps`: `G-4-n`.

## 8. 05_atam_report_draft.json (activity synthesize-and-review)

`atam.py project-draft` writes this file deterministically from 00–04. The stage-5 gate requires the draft to
equal that projection exactly. The projection:

- appends ` (evidence: AE-1, AE-2; basis: observed|inferred)` to every risk and non-risk rationale and to every
  approach rationale and description;
- appends ` (evidence: AE-n)` to sensitivity and tradeoff parameters;
- copies the utility tree, keeping priority tuples only where 02 has observed ones;
- copies `evaluation_inputs` verbatim and takes metadata only from supplied metadata (otherwise null or []);
- merges every gap from 01–04 into `semantic_state.gaps` as `[G-x-n] (gap_type) description`;
- sets `report_status` to `draft`, with evidence that no architect review is recorded.

## 9. Phrasing patterns

| Instead of | Write | Basis |
| --- | --- | --- |
| "There is no failover mechanism." | "The supplied material does not describe a failover mechanism, so availability under node loss is unresolved." | inferred |
| "The system violates the 2 s target." (no measured workload) | "No workload or benchmark is supplied, so whether the 2 s target is met cannot be determined; queueing at the broker is a potential latency risk." | inferred |
| "Latency is adequate." (no measure) | "No response-time target is supplied, so adequacy cannot be determined." | inferred |
| "Messages are persisted to disk (AE-4)." when AE-4 states it | keep, with evidence AE-4 | observed |
| "(evidence: AE-2, G-4-1)" | "(evidence: AE-2)", and keep G-4-1 in gaps | — |
