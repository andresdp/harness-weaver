---
name: check-evaluation
description: Check an ATAM report draft for required sections, evidence links, semantic-state evidence, explicit uncertainty and readiness for architect review. In this harness it is the stage6-check_evaluation procedure used by the atam-evaluation-checker agent, which reviews 05_atam_report_draft.json and writes only 06_review_findings_initial.json. Never computes final readiness and never edits the report; corrections are applied by revise-report in stage 7.
---

# Check an ATAM Evaluation

Use the ATAM methodology profile (`methodology.yaml`) and the report contract (`atam-report.schema.json`). Review the draft against the supplied evaluation inputs.

1. Confirm the report is rooted at `ATAM_Evaluation`, contains metadata and evaluation inputs, and places generated findings under `evaluation_results` with every section the contract requires.
2. Confirm `evaluation_results.semantic_state` uses only the status values the methodology allows and gives evidence for each status. The report stays at `draft` unless a software architect has actually reviewed it. Each gap names its affected activity, missing evidence and a resolution question.
3. Trace each material finding to supplied evidence, and flag unsupported claims and missing references. Each analysis record must reference a source scenario by id or verbatim text.
4. Check that quality attribute scenarios, priority judgments and response measures distinguish evidence from assumptions.
5. Confirm gaps and unresolved questions stay visible. Missing reference data is never treated as a known answer.
6. Return findings and corrections without adding unsupported facts. Mark the report ready for architect review only after structural and evidence checks pass.

## Evidence and readiness rules

- `observed` means the claim is directly stated by the supplied inputs or a validated upstream artifact. A conclusion drawn by reasoning is `inferred`, even when its premises are observed.
- A missing description can support the statement that the supplied material does not establish a fact; it cannot support claiming that the fact is false. Frame such findings as unresolved or potential risks and label them inferred.
- Evidence identifiers and gap identifiers are separate namespaces. Reject any `G-*` identifier in an `evidence_ids` array or evidence citation; gap IDs belong only in gap records.
- If performance evidence has no workload, benchmark, response-time target, or other measure, do not state that a performance target is met or violated.
- Stage the workflow as separate ordered runtime invocations: synthesize draft, review draft, revise once, then calculate final readiness. The review step cannot report final readiness. The final revision step must run even when there are no corrections to make.
- After revision, readiness is false while any `fail` or `warn` remains in structure, semantic state, evidence traceability, uncertainty, method coverage, or reference-boundary checks. A prior `ready_for_architect_review` value is not authoritative; recompute it from the final checks.

## Harness binding (stage6-check_evaluation)

The rules above are the source method and stay normative. In this harness, step 6's "mark the report
ready" belongs to stage 7, which computes readiness in code (`atam.py finalize`). The review stage records
findings and corrections only.

**Reads:** `_workspace/00_evaluation_inputs.json` through `04_analysis.json`, `05_atam_report_draft.json`, and
the contracts in `../evaluate-architecture/references/`.
**Writes only:** `_workspace/06_review_findings_initial.json`, shaped by
`atam_harness/schemas/06_review_findings.schema.json` with `review_stage: "initial"` and
`reviewed_report: "05_atam_report_draft.json"`. It must not contain `revision`, `ready_for_architect_review`
or `readiness_basis`.

### Procedure

1. Run `python3 atam_harness/atam.py check --report _workspace/05_atam_report_draft.json --phase initial`.
   It prints the automated checks: structure, status values, gap fields and visibility, the evidence suffix,
   gap-id leaks, id registration, finding traceability to 04, verbatim scenario references, absence-labelled-as-observed,
   performance attainment wording without a measure, response measures, priority provenance, coverage, and
   the reference boundary. Copy **every** entry into `checks` unchanged. The gate re-runs the command and
   rejects any missing entry, any changed result and any invented automated entry.
2. Then review what code can't judge, reading each finding against the AE/BD/AP statements it cites:
   - **evidence_traceability**: does the cited evidence actually support the claim? Flag any claim that goes
     beyond its evidence, and any material claim that has no evidence.
   - **uncertainty**: is something labelled `observed` actually a reasoned conclusion? Is a conclusion from
     absence framed as fact? Is performance attainment asserted without a workload, benchmark or target,
     including paraphrases the automated lexicon misses? Are fabricated thresholds or priorities treated as
     known?
   - **method_coverage**: are prioritized scenarios analyzed? Are sensitivity and tradeoff points supported?
     Are approaches only those the evidence supports?
   - **semantic_state**: do the status values match their evidence (for example `sufficient` while a material
     gap exists)?
   Add each concern as a `source: "reviewer"` check. Use a `check_id` of the form `<PREFIX>-R<n>`, where the prefix is
   `STRUCT|SEM|EVID|UNC|COV|REF` and matches the category. Give the narrowest JSON-pointer `location` into the
   draft (for example `/ATAM_Evaluation/evaluation_results/analysis_records/2/findings/risks/0/rationale`), a
   `finding`, and a `correction`. A correction may only remove, relabel (observed→inferred), relink to cited
   ids, rephrase or qualify. It must never require new facts. When it can't be fixed without new facts, say
   so and point to the gap that must stay visible.
3. Record at least one reviewer check per category you examined, using `result: "pass"` when it holds, so the
   review shows what was examined. Use `warn` for a concern that needs a change but doesn't break the method,
   and `fail` for a violation of an evidence or method rule.
4. Set `summary` to the counts of pass, warn and fail over all checks, and `run_id` to the ledger's run id
   (`python3 atam_harness/atam.py status`).
5. Validate with `python3 atam_harness/atam.py validate stage6-check_evaluation`.

Don't edit the draft or any upstream artifact. Don't try to "help" by fixing problems here. A review that
silently fixes things leaves no record of what was wrong, and stage 7 exists to apply corrections once,
traceably.
