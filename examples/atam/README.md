# HarnessWeaver ATAM Evaluation Demonstration

This example demonstrates one shared ATAM methodology profile materialized as two runtime forms:

- `claude-plugin/` — a Claude Code plugin with evaluator skills and specialist subagents.
- `deepagents/` — a Python backend using DeepAgents with the same workflow, skills, report template, and evidence boundaries.

## Shared design

- `harnessspec.yaml` describes the workflow, roles, stages, sources, artifacts, and verification.
- `methodology.yaml` makes ATAM activities and semantic methodology state explicit.
- Both runtime forms consume only `ATAM_Evaluation.evaluation_inputs` from `data/banking.json`.
- `ground_truth_outputs` is reserved for evaluation after generation and execution; it must not be passed to either harness.
- `report-template.json` defines the generated report structure. It is derived from `case-studies/architecture-eval/ATAM/template.json` and renames `ground_truth_outputs` to `evaluation_results` so generated findings cannot be confused with reference answers.

The profile is an adaptation for a bounded prototype. It does not claim that a model-generated report is equivalent to a complete, expert-facilitated ATAM evaluation or ready for decision use without architect review.

## Current DeepAgents scope

The DeepAgents backend produces an evidence-grounded ATAM report draft from the case's existing `evaluation_inputs`. Its report contract includes metadata, a utility tree, architectural approaches, scenarios, and scenario analysis records covering risks, non-risks, sensitivity points, and tradeoff points. The coordinator delegates an initial analysis to `quality-attribute-analyst`, then asks `evidence-reviewer` to check coverage and evidence support.

This is a bounded model-led pass, not a full ATAM evaluation. It does not conduct stakeholder presentations or workshops, elicit and validate priorities directly with stakeholders, or run the ATAM activities as explicit, controlled phases. It works from the supplied case evidence, marks gaps and uncertainty, and does not claim that a structurally complete report means the method was fully completed. A software architect must review the draft and resolve material gaps before using it for decisions.

The skills describe the intended ATAM analysis coverage, but the current DeepAgents runtime does not yet enforce completion of each activity as a separate stage. Its generated report should therefore be treated as an analysis aid and starting point for architect-led evaluation.

## Validate and try the Claude plugin

From the repository root:

```bash
claude plugin validate examples/atam/claude-plugin
claude --plugin-dir examples/atam/claude-plugin
```

In Claude Code, invoke `/atam-evaluation:evaluate-architecture` and provide the case's evaluation inputs or an architecture description. Invoke `/atam-evaluation:check-evaluation` to review a draft report.

## Run the DeepAgents backend

Follow `deepagents/README.md`. The runner requires a provider API key and a working DeepAgents installation. It writes only the generated report to the path supplied with `--output`.

## Compare the runtime forms

Run both forms on the same input and record model/runtime settings. Check report structure, source support, method coverage, explicit uncertainty, and architect review separately. Differences in agent delegation, state handling, or skill loading are fidelity findings; this example does not presume runtime equivalence.
