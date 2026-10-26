---
name: evaluate-architecture
description: Conduct an evidence-grounded ATAM evaluation of a supplied software architecture and produce a structured report draft.
---

# Evaluate an Architecture with ATAM

Use the ATAM methodology profile (`methodology.yaml`) and the report contract (`atam-report.schema.json`, with the human-readable `atam-report-template.json`) before analysis. The harness that uses this skill places both next to it. This is a bounded analysis aid; it does not replace a facilitated stakeholder workshop.

## Input

Use only the architecture evaluation inputs supplied for the case: system description, business context, constraints, candidate scenarios and evaluation questions. Never use reference evaluation outputs (`ground_truth_outputs`) as input. If an input file also contains them, stop and ask for an input-only copy.

## Procedure

1. **Establish context.** Record system scope, business drivers, constraints, architecture evidence and open questions. Missing essential context is a gap, not something to invent.
2. **Build the utility tree.** Refine quality attribute drivers into scenarios with stimulus, environment, response and response measure, and priority judgments only where evidence supports them. Unsupported priorities stay unresolved.
3. **Identify architecture approaches** only from supplied evidence. Mark any inference explicitly.
4. **Analyze scenarios.** For each prioritized scenario, analyze it against the architecture approaches and record risks, non-risks, sensitivity points, tradeoff points, rationale and evidence. Reference each scenario by its source id and verbatim text.
   - Set `basis: observed` only when the finding itself is directly stated in the supplied inputs. Set `basis: inferred` when reasoning connects evidence to a conclusion, including conclusions based on a control, measure, or fact not being described. A missing description can establish uncertainty; it does not establish that a control is absent or that a quality threshold is violated.
   - `evidence_ids` are evidence references, not gap references. Use only identifiers allowed by the artifact contract (architecture evidence IDs for architecture claims; supporting approach/business-driver IDs only where allowed). Never put `G-*` gap identifiers in `evidence_ids` or an `(evidence: ...)` citation. Keep gaps in the separate `gaps` array.
   - For performance, do not infer that a target is met or missed from a qualitative proxy alone. If there is no workload, benchmark, response-time target, or other measure, describe only a potential risk and say that attainment cannot be determined.
   - When projecting a finding into the report, preserve its identifiers and basis in the rationale suffix `(evidence: AE-1, AE-2; basis: observed|inferred)`. Do not put gap IDs in that evidence list.
5. **Record semantic state** in `evaluation_results.semantic_state`:
   - `context_status`, `driver_status`, `architecture_evidence_status`: `missing`, `partial` or `sufficient`;
   - `scenario_analysis_status`: `not_started`, `partial` or `reviewed`;
   - `report_status`: `not_started`, `draft` or `reviewed`.

   Give evidence for every status, including evidence that an expected input is absent. Record each material gap with its description, affected activity, missing evidence and resolution question. Completed tasks or agent calls are not methodology evidence. Keep `report_status` at `draft` until a software architect has reviewed the report.
6. **Synthesize the report** rooted at `ATAM_Evaluation` and conforming to the report contract. Put generated findings under `evaluation_results`, keep only evidence-backed findings, and preserve gaps and unknowns.
7. **Check before returning.** Apply the `check-evaluation` skill, revise where needed, and return the draft for architect review.

## Method boundaries

- Do not invent stakeholder priorities, workshop outcomes, attendees or measurements.
- Distinguish observed architecture decisions from inferred approaches.
- Distinguish observed facts from inferred findings: when the evidence supports a concern but not a conclusion about actual behavior, label it inferred and retain the uncertainty.
- Gap IDs (`G-*`) identify missing or conflicting information. They are not evidence IDs and must not be cited as evidence.
- A missing response measure is an open issue, not an invitation to fabricate a threshold.
- Report risks, non-risks, sensitivity points and tradeoff points only when the input supports them.
- Preserve source references for every material finding where the input permits.
