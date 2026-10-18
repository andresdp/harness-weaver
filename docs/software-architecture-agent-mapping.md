# Software-architecture-agent mapping study

**Status:** Read-only mapping; no adapter or nested application code has been changed.

## Provenance and boundary

The case study is a separate Git repository at `case-studies/software-architecture-agent/`, with origin `https://github.com/NicolasMP51/software-architecture-agent.git` and inspected revision `528ae7c`. Its working tree was clean during inspection. This establishes repository provenance, but not permission to change or redistribute it. Keep changes in HarnessWeaver-owned adapter materials until ownership is confirmed.

## Stage and artifact mapping

| Stage | Responsibility | Inputs | Declared artifacts | HarnessSpec representation |
|---|---|---|---|---|
| 1 `stage1-requirements_drivers` | Analyze requirements, identify quality attributes, identify drivers | Project description and functional requirements | `requirements_analysis.json`, `quality_attributes.json`, `drivers.json` | One stage with three ordered tasks and three output contracts; application data lookup remains an adapter input concern. |
| 2 `stage2-solution_design` | Identify pattern candidates, check compatibility, generate alternatives | Stage 1 artifacts | `pattern_candidates.json`, `pattern_compatibility.json`, `alternatives.json` | One stage referencing the Stage 1 artifact IDs, with ordered task outputs. |
| 3 `stage3-alternative_evaluation` | Evaluate alternatives, analyze trade-offs, select an alternative | Stage 1 artifacts and `alternatives.json` | `alternative_evaluation.json`, `trade_off_analysis.json`, `alternative_selection.json` | One stage with explicit upstream artifact references and evidence verification. |
| 4 `stage4-architecture_decision` | Create an ADR and high-level architecture diagram | Stage 3 evaluation, trade-off, and selection artifacts | `adr.md`, `architecture_diagram.mmd` | One stage; mixed Markdown/Mermaid output contracts must be supported by the selected adapter. |

All four stage `AGENTS.md` files require serial task execution and read-back validation. Stages 2–4 document their input artifact dependencies. `pipeline_service.py` separately declares per-stage filenames in `STAGE_ARTIFACTS`; that registry is application wiring, not shared domain intent.

## Adapter and fidelity findings

- `factory.py` constructs a Google Generative AI model and routes `/agent/` reads to a filesystem containing stage definitions while sending other paths to a Firestore-backed project store. Firebase, model credentials, and project storage belong outside HarnessSpec.
- `stages.py` imports the Firebase database at module load and Stage 1 uses project persistence to construct its prompt. A portable spec can describe the input contract, but not this application's authentication and persistence mechanism.
- **Execution blocker:** `get_stage_message(stage_number, project_id)` calls `build_stage1_message(project_id)`, while `build_stage1_message` requires both `user_id` and `project_id`. `PipelineService.run_stage` also calls `get_stage_message(stage_number, project_id)` without a user ID. Stage 1 therefore has a call-contract mismatch in the inspected revision. No fix was applied because this code belongs to the nested repository.
- Stage instructions require artifacts to be written under `/artifacts/`, while `pipeline_service.py` completion checks look up named documents in Firestore. The mapping must confirm that the active backend translates those paths to those documents; the inspected files alone do not prove that contract.
- Stage 4 declares `architecture_diagram.mmd`, but needs target-runtime handling for Mermaid text alongside JSON artifacts.

## Next integration step

After ownership and a Stage 1 contract fix are established by the case-study owner, create a HarnessSpec mapping and adapter tests in the HarnessWeaver repository. Validate stage order, declared artifact names, missing-input behavior, and output routing with external services stubbed. Do not treat the current Stage 1 path as executable evidence.
