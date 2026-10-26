---
name: check-evaluation
description: "Check an ATAM report draft for required sections, evidence links, semantic-state evidence, explicit uncertainty and readiness for architect review."
---

# Check an ATAM Evaluation

Use the ATAM methodology profile (`methodology.yaml`) and the report contract (`atam-report.schema.json`). Review the draft against the supplied evaluation inputs.

1. Confirm the report is rooted at `ATAM_Evaluation`, contains metadata and evaluation inputs, and places generated findings under `evaluation_results` with every section the contract requires.
2. Confirm `evaluation_results.semantic_state` uses only the status values the methodology allows and gives evidence for each status. The report stays at `draft` unless a software architect has actually reviewed it. Each gap names its affected activity, missing evidence and a resolution question.
3. Trace each material finding to supplied evidence, and flag unsupported claims and missing references. Each analysis record must reference a source scenario by id or verbatim text.
4. Check that quality attribute scenarios, priority judgments and response measures distinguish evidence from assumptions.
5. Confirm gaps and unresolved questions stay visible. Missing reference data is never treated as a known answer.
6. Return findings and corrections without adding unsupported facts. Mark the report ready for architect review only after structural and evidence checks pass.

## Harness binding (added by the harness; the method above is unchanged)

**Files.** `methodology.yaml` → `/agent/skills/check-evaluation/references/methodology.yaml`; `atam-report.schema.json` → `/agent/skills/check-evaluation/references/atam-report.schema.json`. The review output contract is `/agent/skills/check-evaluation/references/review-findings.schema.json`.

**Input Artifacts.** Read `/artifacts/05_atam_report.json` (the draft under review), the supplied inputs `/artifacts/00_evaluation_inputs.json`, and the stage artifacts `/artifacts/01_context.json` … `/artifacts/04_analysis.json`, which carry the `source_refs`, `basis` and evidence ids behind each report statement.

This stage runs in a single agent, so this review is not independent of the drafting task. Compensate by checking against the artifacts, not your memory of writing the report: re-open every file before judging it.

**Structural checks by reading.** No code runs in this stage. Set `deterministic_validation` to `{"ran": false, "tool": "none in stage (the host validates the named schemas after the stage)", "exit_code": null, "summary": "..."}`, and check the structure yourself against `/agent/skills/check-evaluation/references/atam-report.schema.json`: required keys, no extra keys, and enum values.

**Checks to record** (`C-n`, one per finding, with `result` = `pass`, `fail` or `warn`). Cover at least one check per category:

| Category | What to check (steps of the method above) |
|---|---|
| `structure` | Step 1: contract conformance, the `ATAM_Evaluation` root, all sections present, and `evaluation_inputs` equal to the supplied inputs |
| `semantic_state` | Step 2: allowed values only; the evidence for each status actually supports the value; `report_status` = `draft`; `scenario_analysis_status` ≠ `reviewed`; gaps are complete with all four fields |
| `evidence_traceability` | Step 3: every risk, non-risk, sensitivity and tradeoff point and every approach traces through its evidence ids to `source_refs` that support it; each analysis record references its scenario by id and verbatim text |
| `uncertainty` | Steps 4–5: assumptions and inferences are labeled; null response measures and priorities are not filled; every stage gap is present in the report |
| `method_coverage` | Every scenario in `02_utility_tree.json.analysis_order` is analyzed or explicitly unanalyzed; the findings types are used appropriately (a sensitivity point is a parameter, not a risk) |
| `reference_boundary` | No `ground_truth_outputs` or other reference answers appear anywhere |

For every `fail` or `warn`, `correction` states the minimal concrete change, and that change never adds a fact (e.g. "Relabel R-3 rationale basis as inferred", "Remove NR-2: no evidence id supports it", "Restore gap G-2-3"). List each statement that cannot be traced to the inputs in `unsupported_claims`.

**Readiness.** `ready_for_architect_review` is `true` only when no check in `structure`, `semantic_state`, `evidence_traceability` or `reference_boundary` remains `fail` after the revision step. `architect_review_focus` lists what the architect should examine first, drawn from the methodology's review focus (method coverage, evidence grounding, risks, tradeoffs, unknowns) and the most consequential gaps.

**Revision record.** On the first pass, write `"revision": {"applied": false, "changed_locations": [], "remaining_failures": [<ids of failing checks>]}`.

The `revise-report` task updates this record after it applies corrections.

**Expected Output.** Write `/artifacts/06_review_findings.json`:

```json
{
  "reviewed_artifact": "05_atam_report.json",
  "deterministic_validation": {"ran": true, "tool": "string", "exit_code": 0, "summary": "string"},
  "checks": [{"id": "C-1", "category": "structure | semantic_state | evidence_traceability | uncertainty | method_coverage | reference_boundary",
              "result": "pass | fail | warn", "location": "JSON path in 05_atam_report.json or 'report'",
              "finding": "string", "correction": "string or null (null when pass)"}],
  "unsupported_claims": [{"location": "string", "claim": "string", "reason": "string"}],
  "revision": {"applied": false, "changed_locations": [], "remaining_failures": ["C-2"]},
  "ready_for_architect_review": false,
  "architect_review_focus": ["string"]
}
```

Read the file back and verify that it parses and that `ready_for_architect_review` is consistent with the remaining failures. Never set `report_status` to `reviewed`: only a software architect's recorded review can do that.
