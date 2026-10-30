# Host adaptation for the SARA pilot

## Decision

Run generated SARA stages with the generic HarnessWeaver DeepAgents stage host. Do not run or modify SARA's application host for this pilot.

## Why

The research question for this exercise is whether HarnessWeaver can harvest and materialize a domain-specific architecture-design workflow. SARA's own `PipelineService` has a known Stage 1 call-contract mismatch: the stage message builder requires both `user_id` and `project_id`, while its caller passes only `project_id`. Using that application path would make the pilot depend on an unrelated SARA integration defect.

## Runtime boundary and expected adaptations

- Keep SARA's four stages in order and preserve each stage's ordered tasks and artifact handoffs.
- Pass the CampusBike project description and functional requirements through ports named `project_description` and `functional_requirements`, matching `cases/campus-bike.yaml`.
- Use the HarnessWeaver host's filesystem artifact store and per-stage JSON Schema validation instead of SARA's Firestore-backed project store and document checks.
- Keep runtime implementation details—Firebase, authentication, frontend/API routing, SARA's model factory and database access—out of the HarnessSpec and generated stage instructions.
- The HarnessWeaver host accepts JSON artifacts. Represent the final ADR as an `adr_markdown` string and the Mermaid diagram as an `architecture_diagram_mermaid` string in `architecture_decision.json`, validated by the pilot contract. This changes the output envelope; it does not claim that SARA itself consumes this package.
- Do not add a new mid-run human gate solely because the host changes. The architect can review the completed outputs after execution; any change to the source workflow's review behavior must be recorded separately.

## Fidelity claim boundary

This run can support a claim about standalone materialization and execution of the harvested SARA workflow under the HarnessWeaver host. It cannot establish drop-in compatibility with SARA, fidelity of Firestore/UI integration, or behavioral equivalence to the original hosted application.

The source packet also contains an artifact-reference inconsistency: the Stage 4 diagram skill asks for `/adr.json`, while the ADR skill declares `/adr.md`. Preserve and report this defect. The generated workflow should use a consistent HarnessWeaver-side handoff and identify the correction as an adaptation.
