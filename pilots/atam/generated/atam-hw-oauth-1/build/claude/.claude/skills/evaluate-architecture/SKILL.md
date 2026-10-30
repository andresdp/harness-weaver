---
name: evaluate-architecture
description: "Conduct an evidence-grounded ATAM evaluation of a supplied software architecture and produce a structured report draft. Method reference for the atam-evaluation pipeline; to run an evaluation use the atam-evaluation orchestrator."
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
- A missing response measure is an open issue, not an invitation to fabricate a threshold.
- Report risks, non-risks, sensitivity points and tradeoff points only when the input supports them.
- Preserve source references for every material finding where the input permits.

## Harness binding (added by the harness; the method above is unchanged)

**Files.** `methodology.yaml` → `.claude/skills/evaluate-architecture/references/methodology.yaml`; `atam-report.schema.json` → `.claude/skills/evaluate-architecture/references/atam-report.schema.json`; `atam-report-template.json` → `.claude/skills/evaluate-architecture/references/atam-report-template.json`.

**How this project runs the method.** The `atam-evaluation` orchestrator skill runs the procedure as a five-stage pipeline. Each step has one agent and one task skill, and the steps exchange JSON artifacts under `_workspace/`:

| Step | Task skill | Agent | Artifact |
|---|---|---|---|
| Input check | `atam-evaluation` step 1 (`validate_artifacts.py prepare-input`) | orchestrator | `00_evaluation_inputs.json` |
| 1. Establish context | `atam-establish-context` | `atam-context-analyst` | `01_context.json` |
| 2. Build the utility tree | `atam-build-utility-tree` | `atam-utility-tree-analyst` | `02_utility_tree.json` |
| 3. Identify approaches | `atam-identify-approaches` | `atam-approach-analyst` | `03_approaches.json` |
| 4. Analyze scenarios | `atam-analyze-scenarios` | `atam-scenario-analyst` | `04_analysis.json` |
| 5–6. Semantic state and report | `atam-synthesize-report` | `atam-report-synthesizer` | `05_atam_report.json` |
| 7. Check before returning | `check-evaluation` | `atam-evaluation-reviewer` | `06_review_findings.json` |

Read this skill for the method and its boundaries; each task skill holds that step's artifact contract. To evaluate an architecture, use `atam-evaluation`, not this skill directly.
