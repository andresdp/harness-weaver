# Design notes: sara-architecture-design

- Spec: `harnessspec.yaml` (spec_version 0.2, revision 0.1.0, 2026-10-29). `hw validate` passes; capability check passes for `sequential_stages`, `filesystem_artifacts`, `skills`, `json_schema_validation`.
- Procedure: harvest (G0 `start_from: harvest:sources/harvest-input`) → design → DeepAgents target.
- Design inputs: the SARA source packet (`sources/harvest-input/`, copied verbatim to `sources/domain/`), `../sources/host-adaptation.md`, and `contracts/architecture-decision.schema.json`. No execution case data was read or used.

## Gate answers

| Gate | Question | Answer | Source |
|---|---|---|---|
| G0 | Authoritative sources? | `sources/` | harness-answers.yaml |
| G0 | Starting point? | harvest from `sources/harvest-input` | harness-answers.yaml |
| G0 | Saved HarnessSpec or brief? | Saved spec (`harnessspec.yaml`). The answers file's `saved_spec: false` is overridden by the request. | user (live) |
| G0 | Output root? | `generated/` | harness-answers.yaml |
| G0 | Draft sources accepted after harvest review? | Accepted as written | user (live) |
| G1 | D6: Stage 4 inputs? | Add requirements_analysis, quality_attributes, drivers, alternatives as read-only Stage 4 inputs (adaptation A6) | user (live) |
| G1 | Where to assess semantic checkpoints? | Post-run verification only; no new task or artifact (A8) | user (live) |
| G2 | Coordination pattern? | sequential pipeline, 4 stages × serial tasks | harness-answers.yaml; evidence: stage AGENTS.md |
| G2 | Stage boundaries? | SARA's four stages, unchanged | user request (`prompt.md`) |
| G2 | Verification approach? | producer read-back per task + host schema validation per stage + post-run deterministic cross-reference checks + post-run architect review | design choice from evidence (stage AGENTS.md, host-adaptation.md) |
| G3 | Contracts? | use the supplied final contract; intermediate schemas derived from SARA's JSON structure blocks | harness-answers.yaml |
| G4 | Targets? | DeepAgents | harness-answers.yaml |
| G4 | Output directory? | `generated/build/deepagents/` (default, next to the spec) | default |
| G5 | DeepAgents host? | HarnessWeaver stage host | harness-answers.yaml; host-adaptation.md |
| G5 | Human-in-the-loop? | Disabled at run time; no `human_gates` in `wiring.yaml`. Architect review is recorded in the spec as a post-run review outside the harness run. | harness-answers.yaml; user (live, revision 2) |
| G5 | Stage 4 final envelope? | No separate packaging task. The host CLI exposes no assembly step, so SARA's architecture-diagram task writes `architecture_decision.json` (A7). | user (live, revision 2); evidence: host `--help` |
| G5 | Subagents? | no | harness-answers.yaml |
| G5 | Model? | not pinned; env-driven at execution | user (live) |
| G6 | Write confirmation | First confirmed, then withdrawn before the target was complete; the partial bundle was deleted at the user's request. Revised plan confirmed: two Stage 4 tasks, no runtime HITL, post-run cross-reference and package-fidelity checks are manual. | user (live) |

**Conflict (G0 saved_spec).** The answers file says `saved_spec: false`, but the request asks for a HarnessSpec under `generated/`, and the work is multi-stage and evaluated. Resolved by the user: keep the saved spec.

## Designs considered (G2)

1. **SARA's four stages, serial tasks, one deep agent per stage (chosen).** Maps 1:1 onto the stage host; preserves stage boundaries, task order, dependencies and artifact handoffs as the request requires.
2. Split Stage 3 selection into its own reviewer stage. Rejected: SARA has no independent reviewer; adding one would change the method.
3. Merge Stages 3 and 4. Rejected: violates the required stage boundaries; Stage 4 is explicitly "documentation only".

## Key design decisions

- **Artifact names.** SARA's filenames are kept (`requirements_analysis.json`, …) under one location, `/artifacts/` (A4, defect D3), instead of the `{NN}_{step}.json` convention, to preserve artifact identity with the source.
- **Stage 4 envelope (A2, A3, A5, A7; revision 2).** The HarnessWeaver host CLI (`--bundle --input --workspace --out --model [--timeout] [--continue-past-gates]`) validates stage artifacts and copies the one declared output artifact; it has no deterministic assembly or transform step. SARA's two Stage 4 tasks, as written, emit two separate non-JSON files and neither writes the Stage 3 selection id or rationale, so they cannot produce the four-key envelope unchanged. Choice: keep SARA's two tasks. ADR generation writes `adr.json` (`selected_alternative_id`, `adr_markdown`), the handoff the diagram task reads (fixes D2 on the HarnessWeaver side). The diagram task writes `architecture_decision.json` with its Mermaid source and with the selection id, selection rationale and ADR copied unchanged. Copy drift is checked by `v-package-fidelity`, a **manual** post-run comparison; no executable checker is generated. A separate packaging task (revision 1) was dropped.
- **Human review (revision 2).** No runtime gate. `wiring.yaml` declares no `human_gates`, because the host stops at declared gates (`--continue-past-gates` would only record them as bypassed). `architect-review` stays in the spec as a post-run review.
- **Intermediate schemas.** Required keys mirror each SARA JSON structure block; extra keys are allowed; only SARA's explicit evaluation scale is an enum. No identifiers were added (D7 preserved).
- **Semantic state.** Five inferred checkpoints, all `unknown` at design time; assessed post-run only.
- **Spec-format limits.** The 0.2 schema has no field for stage dependencies or within-stage task order; both are stated in each stage's `purpose` and `readiness` and in `sources/methodology.yaml`.

## Assumptions and open questions

- The stage host writes each input port to `/artifacts/00_<port>.json`; the content shape of a port file is the host's choice, so the port schemas are permissive and are not named in `wiring.yaml`.
- The model is supplied at execution through the host's required `--model` argument.
- Semantic checkpoints and the human-review need are inferred, not stated by SARA.

## Change history

| Date | Change | Target | Reason |
|---|---|---|---|
| 2026-10-29 | Initial harvest, spec 0.1.0 | — | SARA pilot |
| 2026-10-29 | Revision 2: packaging task removed (diagram task writes the final envelope); runtime gate removed from the planned wiring; `architecture_diagram` intermediate artifact and schema dropped | — | User feedback before materialization |
| 2026-10-29 | Revision 3: post-run cross-reference and package-fidelity checks declared manual; partial bundle deleted; target rematerialized | deepagents | User G6 answer |
