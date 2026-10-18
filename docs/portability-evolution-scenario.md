# Portability and evolution scenario

This scenario records the HarnessWeaver-owned procedure for U7. It is ready to execute after the paired ATAM pilot produces review feedback.

## Portable-skill case

- **Consumer:** Codex, as the non-Claude coding agent.
- **Input:** `examples/atam/harnessspec.yaml` and `case-studies/atam-evaluator/archevaluation-llms/input-artifacts/G1-anonymized-blind-eng.pdf`.
- **Fixed request:** “Using this HarnessSpec and the supplied architecture evaluation document, prepare the declared workflow input and identify the runtime artifacts the selected skill-based adapter can create. Do not invent unsupported agent tools. Report each unsupported capability and preserve the source path as provenance.”
- **Evidence to record:** skill invocation, source document path/hash, produced artifact paths, validation output, manual substitutions, and unsupported capabilities. Do not claim that reading a document constitutes successful architecture evaluation.

## Feedback-driven evolution case

1. Select one bounded, evidence-backed issue from the blinded reviewer notes of the U5 banking run.
2. State whether the issue belongs to shared workflow intent (HarnessSpec), domain guidance, or runtime mechanics (adapter/harness).
3. Preserve the original spec, harness, run, and reviewer record. Create a new version linked to the feedback record.
4. Rerun the same case and protocol with matched settings. Apply the same deterministic checks and blind review.
5. Report the targeted criterion, any improvement, any regression, and any unavailable measurement. If U5 has no reviewer feedback, defer the evolution run rather than fabricate a lesson.

This file defines the scenario; no portability run or evolution comparison is claimed yet.
