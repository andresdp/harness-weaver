Build an agent harness that performs an evidence-grounded ATAM architecture evaluation, using the materials in `sources/` (start with `sources/intent.yaml`, `sources/methodology.yaml` and `sources/domain/`).

Treat the source methodology's evidence rules and every supplied artifact contract as normative. In particular, use the supplied `sources/domain/contracts/analysis.schema.json` for the scenario-analysis artifact: `evidence_ids` must match its allowed evidence namespaces, and `G-*` identifiers may appear only in gap records.

The generated workflow must distinguish observed facts from inferred findings in both structured artifacts and reports. A conclusion based on an absence in the supplied material is an inference about uncertainty, not an observed fact. A qualitative performance proxy without a workload, benchmark, or response-time target cannot establish that a target is met or violated.

In the final report, every risk and non-risk rationale must preserve its evidence identifiers and basis using the exact suffix format `(evidence: AE-1, AE-2; basis: observed|inferred)`. Never place `G-*` identifiers in an evidence citation.

Materialize report synthesis, report checking, and the single report-revision pass as three distinct, ordered runtime stages named `stage5-synthesize_report`, `stage6-check_evaluation`, and `stage7-revise_report`. Stage 5 writes only `05_atam_report_draft.json`; stage 6 reviews that draft and writes only `06_review_findings_initial.json`; stage 7 reads both and writes the final `05_atam_report.json` and `06_review_findings.json`. The revision stage must execute after the review stage on every run, including when no correction is needed. It alone computes final `ready_for_architect_review`; that value must remain false while any blocking fail or warning remains. Do not implement these as three checklist items that one model response can skip.

Treat `generated/` as the project directory: write every file you create under `generated/`, and nothing anywhere else. The harness will later run on architecture evaluation inputs that are not part of `sources/`; do not look for or invent case data.

Ask me whatever you need to decide before writing files.
