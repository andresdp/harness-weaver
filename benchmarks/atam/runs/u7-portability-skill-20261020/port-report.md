# ATAM portable-skill case report

## Outcome

Prepared a generation input from the supplied architecture document and mapped the v0.1 ATAM HarnessSpec to a five-stage portable-skill target. The input includes the page 1 text and a manual transcription of its diagram. The diagram transcription is explicitly unreviewed and partial. No ATAM evaluation was run and no claim is made about generated findings, accuracy, or runtime behavior.

## Provenance and validation

- Source PDF: `case-studies/atam-evaluator/archevaluation-llms/input-artifacts/G1-anonymized-blind-eng.pdf`.
- Source SHA-256: `8d1dedb86e9ad3b334276cd666cdcd05b1b4857d02a97e21a771812a13b3ba22`.
- Extracted input text: `benchmarks/atam/runs/u7-portability-skill-20261020/source-architecture.txt` (page 1 only; SHA-256 `2d62ea75dee96da72716645a3e22e2dfe688108827e148d13aee1cd630c70366`).
- Prepared HarnessSpec-shaped input: `benchmarks/atam/runs/u7-portability-skill-20261020/evaluation_input.json`.
- Prepared input SHA-256: `9eb54167782c5cdc851e052c7cba635ce229adcb9acb7d01ceb1c828ea09fb0f`.
- Page 1 diagram transcription: `benchmarks/atam/runs/u7-portability-skill-20261020/diagram-transcription.md`; manual, partial, and unreviewed.
- HarnessSpec: `examples/atam/harnessspec.yaml`, version 0.1, SHA-256 `8f10df84b956ba2a9929b51a2f77725a54f7990819256fc092512ffeaedb250e`.
- Validation: source JSON parsed; the HarnessSpec validator accepted v0.1 with the declared `file-based artifact input and output` capability. The input uses the expected `ATAM_Evaluation.evaluation_inputs` envelope.

## Mapping decisions and fidelity

- The supplied document is a combined source: page 1 presents the architecture; later pages include utility-tree and ATAM evaluation material. The prepared input includes the page 1 text plus a separate manual diagram transcription; later material was excluded to avoid giving the generation stage existing evaluation outputs. The transcription does not capture every connector and needs source review.
- The HarnessSpec references the banking JSON as its input source, while this scenario requests the supplied PDF. For this portability case, the PDF was a documented manual input substitution. The shared HarnessSpec was not edited.
- The target mapping is five ordered stages: context, utility tree, architecture approaches, scenario analysis, synthesis/review. The manifest lists their proposed JSON artifacts.
- The current DeepAgents sequential path now calls the same five stage IDs and validates Pydantic handoffs, but intermediate artifacts remain in memory. It writes the final report and runtime fidelity sidecar. A file-backed skill adapter would need to persist and read back each intermediate JSON file.
- Skills do not create tools by themselves. No Claude-specific tool, messaging, workflow script, or persistent peer-collaboration behavior is claimed for the portable-skill target.

## Not verified

- No Codex skill trigger or near-miss test was run in a live consumer session.
- No target stage directories were materialized, no LLM was invoked, and no final ATAM report was generated from this source. The diagram transcription remains unreviewed and should not be treated as authoritative.
- Read-back validation of per-stage files and expert review of any evaluation output remain untested.
