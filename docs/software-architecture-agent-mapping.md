# Software-architecture-agent mapping study

**Status:** Read-only mapping; no adapter or nested application code has been changed. The SARA pilot now selects the generic HarnessWeaver stage host for its first standalone run; see [the pilot decision](../pilots/sara/sources/host-adaptation.md).

## Provenance and boundary

The case study is a separate Git repository at `case-studies/software-architecture-agent/`, with origin `https://github.com/NicolasMP51/software-architecture-agent.git` and inspected revision `528ae7c`. Its working tree was clean during inspection. This establishes repository provenance, but not permission to change or redistribute it. Keep changes in HarnessWeaver-owned adapter materials until ownership is confirmed.

## Stage and artifact mapping

| Stage | Responsibility | Inputs | Declared artifacts | HarnessSpec representation |
|---|---|---|---|---|
| 1 `stage1-requirements_drivers` | Analyze requirements, identify quality attributes, identify drivers | Project description and functional requirements | `requirements_analysis.json`, `quality_attributes.json`, `drivers.json` | One stage with three ordered tasks and three output contracts; application data lookup remains an adapter input concern. |
| 2 `stage2-solution_design` | Identify pattern candidates, check compatibility, generate alternatives | Stage 1 artifacts | `pattern_candidates.json`, `pattern_compatibility.json`, `alternatives.json` | One stage referencing the Stage 1 artifact IDs, with ordered task outputs. |
| 3 `stage3-alternative_evaluation` | Evaluate alternatives, analyze trade-offs, select an alternative | Stage 1 artifacts and `alternatives.json` | `alternative_evaluation.json`, `trade_off_analysis.json`, `alternative_selection.json` | One stage with explicit upstream artifact references and evidence verification. |
| 4 `stage4-architecture_decision` | Create an ADR and high-level architecture diagram | Stage 3 evaluation, trade-off, and selection artifacts | `adr.md`, `architecture_diagram.mmd` | One stage. The standalone HarnessWeaver host accepts JSON artifacts, so the pilot packages the ADR Markdown and Mermaid source as strings in a schema-validated `architecture_decision.json`. This changes the output envelope and is reported as a pilot adaptation. |

All four stage `AGENTS.md` files require serial task execution and read-back validation. Stages 2–4 document their input artifact dependencies. `pipeline_service.py` separately declares per-stage filenames in `STAGE_ARTIFACTS`; that registry is application wiring, not shared domain intent.

## Adapter and fidelity findings

- `factory.py` constructs a Google Generative AI model and routes `/agent/` reads to a filesystem containing stage definitions while sending other paths to a Firestore-backed project store. Firebase, model credentials, and project storage belong outside HarnessSpec.
- `stages.py` imports the Firebase database at module load and Stage 1 uses project persistence to construct its prompt. A portable spec can describe the input contract, but not this application's authentication and persistence mechanism.
- **Execution blocker:** `get_stage_message(stage_number, project_id)` calls `build_stage1_message(project_id)`, while `build_stage1_message` requires both `user_id` and `project_id`. `PipelineService.run_stage` also calls `get_stage_message(stage_number, project_id)` without a user ID. Stage 1 therefore has a call-contract mismatch in the inspected revision. No fix was applied because this code belongs to the nested repository.
- Stage instructions require artifacts to be written under `/artifacts/`, while `pipeline_service.py` completion checks look up named documents in Firestore. The mapping must confirm that the active backend translates those paths to those documents; the inspected files alone do not prove that contract.
- Stage 4's ADR skill declares `/adr.md`, but the diagram skill asks it to read `/adr.json`. The harvested source packet preserves both files; the standalone HarnessWeaver materialization must document and resolve this mismatch without changing SARA's nested repository.
- Stage 4 declares Markdown and Mermaid outputs, while the HarnessWeaver stage host validates JSON artifacts. The pilot wraps both text outputs in `architecture_decision.json`; the run does not test how SARA's original UI or Firestore integration handles those files.

## Selected standalone pilot adaptation

The first SARA exercise uses `examples/campus-bike/`, the same case used in the ReArch paper. The run-time binding contains only `system_description.txt` and `requirements.json`; empty `qualities.json`, prior decisions, generated outputs, workflow state, and vector databases are excluded. The case binding records file hashes and input provenance.

The generated stages run on the generic HarnessWeaver DeepAgents host, which preserves sequential stage execution and uses filesystem hand-offs plus per-stage JSON Schema validation. It does not exercise SARA's `PipelineService`, Firestore, API, frontend, authentication, or model factory. The Stage 1 call-contract mismatch therefore does not block the standalone run, but remains an upstream SARA defect and a blocker for an integration claim. This setup supports a workflow-transfer/materialization result, not drop-in SARA compatibility.

## Next integration step

For the standalone pilot, generate and review the harvested sources and HarnessSpec, check the DeepAgents bundle, and run it on the CampusBike binding. Keep the SARA-host integration separate: after ownership and the Stage 1 contract fix are established by the case-study owner, validate stage order, declared artifact names, missing-input behavior, and output routing with external services stubbed. Do not treat the standalone run as evidence that the current SARA `PipelineService` path is executable.
