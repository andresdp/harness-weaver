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

The profile is an adaptation for a bounded prototype. It does not claim that a model-generated report is equivalent to an expert-facilitated ATAM workshop or ready for decision use without architect review.

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
