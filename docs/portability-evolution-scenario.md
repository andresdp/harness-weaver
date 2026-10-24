# Portability and evolution scenario

This file records two independent U7 procedures: a portable-skill case that can run from its declared inputs, and a feedback-driven evolution case that requires reviewer feedback.

## Portable-skill case

- **Consumer:** Codex, as the non-Claude coding agent.
- **Input:** `pilots/atam/harnessspec.yaml` and `case-studies/atam-evaluator/archevaluation-llms/input-artifacts/G1-anonymized-blind-eng.pdf`.
- **Fixed request:** “Using this HarnessSpec and the supplied architecture evaluation document, prepare the declared workflow input and identify the runtime artifacts the selected skill-based adapter can create. Do not invent unsupported agent tools. Report each unsupported capability and preserve the source path as provenance.”
- **Evidence to record:** skill invocation, source document path/hash, produced artifact paths, validation output, manual substitutions, and unsupported capabilities. Do not claim that reading a document constitutes successful architecture evaluation.

### Recorded preparation run

- Run artifacts: `benchmarks/atam/runs/u7-portability-skill-20261020/` (ignored local run data).
- Prepared `system_description` from page 1 text and added a separate manual, unreviewed diagram transcription to `evaluation_inputs`. Later pages contain evaluation material and were excluded. The diagram transcription omits unclear connector details and is not authoritative pending review.
- The prepared input passed `AtamCaseDocument` Pydantic validation; `conda run -n harness hw validate pilots/atam/harnessspec.yaml --capability 'file-based artifact input and output'` accepted HarnessSpec v0.1.
- The source PDF path/hash, extracted text, JSON input, five-stage target manifest, and mapping report are recorded in that run directory.
- This was input preparation and adapter mapping only: no skill trigger test, target-stage execution, LLM call, report generation, or expert evaluation was performed. The PDF-to-case conversion is a documented manual substitution because the spec currently points at the separate banking JSON input.

## Feedback-driven evolution case

Run this case only after the paired ATAM pilot produces reviewer feedback.

1. Select one bounded, evidence-backed issue from the blinded reviewer notes of the U5 banking run.
2. State whether the issue belongs to shared workflow intent (HarnessSpec), domain guidance, or runtime mechanics (adapter/harness).
3. Preserve the original spec, harness, run, and reviewer record. Create a new version linked to the feedback record.
4. Rerun the same case and protocol with matched settings. Apply the same deterministic checks and blind review.
5. Report the targeted criterion, any improvement, any regression, and any unavailable measurement. If U5 has no reviewer feedback, defer the evolution run rather than fabricate a lesson.

The portable-skill input-preparation run is recorded above. No feedback-driven evolution comparison is claimed; it remains dependent on reviewer feedback.
