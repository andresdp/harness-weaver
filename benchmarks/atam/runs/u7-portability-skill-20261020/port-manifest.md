# ATAM portable-skill adapter manifest

## Source and prepared input

- HarnessSpec: `examples/atam/harnessspec.yaml` (v0.1; SHA-256 `8f10df84b956ba2a9929b51a2f77725a54f7990819256fc092512ffeaedb250e`).
- Prepared input: `benchmarks/atam/runs/u7-portability-skill-20261020/evaluation_input.json`.
- Source: `case-studies/atam-evaluator/archevaluation-llms/input-artifacts/G1-anonymized-blind-eng.pdf` (SHA-256 `8d1dedb86e9ad3b334276cd666cdcd05b1b4857d02a97e21a771812a13b3ba22`).
- Preparation extracts page 1 text as `system_description` and includes a separate, manual, unreviewed transcription of its architecture diagram. Later pages contain utility-tree and ATAM evaluation material and are excluded from generation input.

## Declared workflow to target stages

| Spec stage | Target directory | Ordered skill | JSON artifact | Input/handoff |
| --- | --- | --- | --- | --- |
| `establish-context` | `stage1-establish-context/` | `establish-context` | `01_evaluation_context.json` | Prepared `evaluation_inputs` |
| `build-utility-tree` | `stage2-build-utility-tree/` | `build-utility-tree` | `02_utility_tree.json` | Stage 1 context and prepared inputs |
| `identify-approaches` | `stage3-identify-approaches/` | `identify-approaches` | `03_architecture_approaches.json` | Stage 1 context, stage 2 utility tree, and prepared inputs |
| `analyze-scenarios` | `stage4-analyze-scenarios/` | `analyze-scenarios` | `04_analysis_records.json` | Prior artifacts and prepared inputs |
| `synthesize-and-review` | `stage5-synthesize-and-review/` | `synthesize-and-review` | `05_atam_report.json` | Stages 1–4 and prepared inputs |

These names describe the portable-skill target pattern. This run did not materialize those five stage directories or call an LLM.

## Existing DeepAgents runtime artifacts

- `examples/atam/deepagents/atam_harness/orchestration.py` maps sequential calls to the five declared stage IDs and validates each returned Pydantic artifact before handoff.
- The runtime `ArtifactEnvelope` carries intermediate JSON values in memory. It does not currently persist one JSON file per intermediate stage.
- `examples/atam/deepagents/atam_harness/reports.py` writes the final ATAM report and a session-matched `.runtime.json` fidelity record.
- The runtime can read the existing `skills/` tree through its virtual filesystem backend; it does not generate or write skills during a run.

## Runtime wiring handoff

- Stage registry and handoff prompts: the five rows above; stage order comes from `HarnessSpec.stages`.
- Expected artifacts: one JSON artifact listed for each stage; stop before final report publication if any stage output fails its Pydantic contract.
- Definitions: mount stage `AGENTS.md` and `skills/` read-only under `/agent/`; route `/artifacts/` to the run artifact store.
- Required application work for a file-backed target: persist each typed stage output as its declared JSON artifact and read it back before advancing. The current example runtime passes validated models in memory instead.
- Unsupported or unverified behavior: this run did not test a skill-triggering consumer, execute a target stage, or verify read-back from a file-backed artifact store.
