# Design notes: archeval-atam-harness

- Spec: `harnessspec.yaml` (spec_version 0.2), validated with `hw validate` (valid; capabilities `file-artifacts`, `skills`, `sequential-stage-execution`, `json-schema-validation` assessed).
- Sources: `sources/` is a verbatim snapshot of the authoritative pilot sources (`intent.yaml`, `methodology.yaml`, `domain/`), copied so the project is self-contained. No case data or reference outputs were read or copied.
- Date: 2026-10-25.

## Gate answers

| Gate | Question | Answer | Source |
|---|---|---|---|
| G0 | Authoritative sources | `sources/` (intent, methodology, domain) | harness-answers.yaml |
| G0 | Starting point | none (fresh build) | harness-answers.yaml |
| G0 | Saved spec or brief | saved HarnessSpec | harness-answers.yaml |
| G0 | Output location | `generated/` (spec at root, targets under `build/<target>/`) | harness-answers.yaml |
| G1 | Scope | Bounded, evidence-grounded ATAM evaluation draft from a supplied case; no claim of conducting workshops or a full expert-facilitated ATAM | harness-answers.yaml |
| G1 | Human review | A software architect familiar with the evaluated system reviews the draft and material gaps before it informs a decision | harness-answers.yaml |
| G1 | Case boundary | Generation-time assets stay case-independent; no case data or evaluator-only outputs in the generated project | harness-answers.yaml |
| G1 | Input port form | One JSON file holding `ATAM_Evaluation.evaluation_inputs` plus optional `metadata`/`title`; inputs containing `ground_truth_outputs` or `evaluation_results` are rejected | user (live) |
| G2 | Stage split / coordination | 5-stage sequential pipeline, one stage per methodology activity; producer-reviewer inside stage 5 with one revision pass; deterministic schema and cross-reference checks | user (live) |
| G3 | Contracts | Use the supplied report schema unchanged; add JSON Schemas for 00–04 and 06 (accepted artifact table) | harness-answers.yaml + user (live) |
| G3 | When may `scenario_analysis_status` be `reviewed`? | Never by the harness; only a recorded architect review | user (live) |
| G4 | Targets | claude, deepagents; output root `generated/` | harness-answers.yaml |
| G5 | Claude execution mode | Sub-agent delegation (one-shot custom agents, JSON files in `_workspace/`) | user (live) |
| G5 | Claude models | Default tiering (opus for analysis and review, sonnet for extraction and assembly) | user (live) |
| G5 | DeepAgents host / model / HITL / subagents | harnessweaver stage host / `openai:gpt-5.4-mini` / none / not allowed | harness-answers.yaml |
| G6 | Write both targets with the listed approximations (DeepAgents review not independent; cross-ID checks only instructed on DeepAgents; H1 not enforced on DeepAgents; stage 2/3 parallel only on Claude) | confirmed | user (live) |

## Designs considered (G2)

1. **5-stage pipeline (chosen).** One stage per methodology activity, so each activity has its own readiness check, artifact and semantic-state contribution. Small stages also suit the single mid-size model on DeepAgents, and the stages map 1:1 to DeepAgents stage directories.
2. 3-stage pipeline (discovery, analysis, synthesis+review). Fewer handoffs, but readiness is checked less often and stage 1 gets large.
3. Single producer + reviewer. Closest to the source skills, but gives the weakest view of progress per activity.

## Key design decisions

- **Roles are not simulated stakeholders.** The ArchEval Customer/Architect/Manager/EvaluationTeam protocol is not reproduced: the Customer is the input port, and the Architect is the human gate. This follows the intent's exclusion of simulated workshops.
- **Evidence linkage.** Intermediate items carry `basis` (`observed` / `inferred` / `assumption`) and `source_refs` (JSON paths into `00_evaluation_inputs.json`), plus ID links (BD-, AE-, AP-, AR-, R-, NR-, S-, T-, G-). The report contract has no evidence fields (`additionalProperties: false`), so stage 5 folds evidence ids into `rationale`/`reasoning` text as `(evidence: …)`.
- **Gap typing.** Intermediate gaps add `id` and `gap_type` (unknown, conflict, incomplete, assumption). The report gap has only the four methodology fields, so stage 5 prefixes the type in the description (e.g. `[conflict] …`).
- **Semantic state ceiling.** The harness writes at most `partial` for `scenario_analysis_status` and `draft` for `report_status`. Moving either to `reviewed` needs a recorded architect review (human gate H1).
- **Retry policy.** A stage whose artifact fails verification is retried once with the failure output; a second failure stops the pipeline. Downstream stages are not run on invented substitutes.
- **Parallelism.** `identify-approaches` depends only on inputs and context. The Claude target runs it alongside `build-utility-tree`; DeepAgents serializes it (stage 3 after stage 2). Both satisfy the same dependencies.

## Assumptions

- Run-time inputs follow the ArchEval `evaluation_inputs` shape (see `sources/domain/references/atam-report-template.json`). The stages read it defensively: keys may be missing, and missing keys become gaps.
- The DeepAgents host validates the JSON Schemas named in `wiring.yaml` after each stage; the generated stages do not execute code.

## Open questions

- Is a single-pass revision in stage 5 enough, or should failing reviews loop until clean? (Default: one pass, remaining failures stay visible in `06_review_findings.json`.)
- No execution run on a real case was performed at generation time; task quality is unverified (spec gap `GAP-no-execution-run`).

## Change history

| Date | Change | Target | Reason |
|---|---|---|---|
| 2026-10-25 | Initial HarnessSpec, contracts and both targets | all | Fresh build |

## Generation results (2026-10-25)

- `hw validate harnessspec.yaml`: valid (spec sha256 f35ed8f1…).
- `hw check-bundle build/claude --target claude --spec harnessspec.yaml`: passes.
- `hw check-bundle build/deepagents --target deepagents --spec harnessspec.yaml`: passes.
- `scripts/validate_artifacts.py` (copied into the Claude bundle) was exercised on a synthetic placeholder fixture in a scratch directory outside `generated/`. It accepted the happy path and caught the reference leak (exit 3) plus 7 injected defects, with and without `jsonschema`. No case data was used.
- The JSON structure block of every task skill was checked against its schema's key structure (both targets: OK).
- These are validation results, not task-quality results. No evaluation case was run.
