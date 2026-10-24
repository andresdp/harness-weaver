# HarnessWeaver ATAM Evaluation Demonstration

This example demonstrates one shared ATAM methodology profile materialized as two runtime forms:

- `claude-plugin/` — a Claude Code plugin with evaluator skills and specialist subagents.
- `deepagents/` — a Python backend using DeepAgents with the same workflow, skills, report template, and evidence boundaries.

## Shared design

- `harnessspec.yaml` describes the workflow, roles, stages, sources, artifacts, and verification.
- `methodology.yaml` makes ATAM activities and semantic methodology state explicit.
- Both runtime forms consume only `ATAM_Evaluation.evaluation_inputs` from `case-studies/architecture-eval/ATAM/data/banking.json`.
- `ground_truth_outputs` is reserved for evaluation after generation and execution; it must not be passed to either harness.
- `report-template.json` defines the generated report structure. It is derived from `case-studies/architecture-eval/ATAM/template.json` and renames `ground_truth_outputs` to `evaluation_results` so generated findings cannot be confused with reference answers.
- `evaluation_results.semantic_state` records evidence-backed methodology status and explicit gaps. Agent calls and completed runtime tasks do not establish method progress; generated reports remain drafts until an architect reviews them.

The profile is an adaptation for a bounded prototype. It does not claim that a model-generated report is equivalent to a complete, expert-facilitated ATAM evaluation or ready for decision use without architect review.

## Current DeepAgents scope

The DeepAgents backend produces an evidence-grounded ATAM report draft from the case's existing `evaluation_inputs`. Its report contract includes metadata, a utility tree, architectural approaches, scenarios, and scenario analysis records covering risks, non-risks, sensitivity points, and tradeoff points. The v0.2 HarnessSpec supports a supervisor with one-shot specialists, a sequential pipeline with typed artifact handoffs, and parallel specialist fan-out with a typed join. These are runtime coordination choices; the pipeline stages do not imply that every ATAM activity, workshop, or stakeholder interaction has been completed.

This is a bounded model-led pass, not a full ATAM evaluation. It does not conduct stakeholder presentations or workshops, elicit and validate priorities directly with stakeholders, or run the ATAM activities as explicit, controlled phases. It works from the supplied case evidence, marks gaps and uncertainty, and does not claim that a structurally complete report means the method was fully completed. A software architect must review the draft and resolve material gaps before using it for decisions.

All modes preserve the supplied-input boundary, shared report schema, and common evaluation skills. The supervisor follows the existing delegated-agent prompt; the other modes use explicit stage/specialist prompts because coordination is external to their agents. Their reports should be treated as analysis aids and starting points for architect-led evaluation. Mode differences are fidelity and quality evidence, not proof of runtime equivalence.

## Validate and try the Claude plugin

The generated plugin and instructions for later Claude validation and generation experiments are in [`CLAUDE-TESTING.md`](CLAUDE-TESTING.md). Live Claude testing is deferred; structural plugin validation can be run from the repository root:

```bash
claude plugin validate pilots/atam/claude-plugin
claude --plugin-dir pilots/atam/claude-plugin
```

In Claude Code, invoke `/atam-evaluation:evaluate-architecture` and provide an evaluation-input-only case file or an architecture description. Invoke `/atam-evaluation:check-evaluation` to review a draft report. Do not provide `ground_truth_outputs` to either plugin skill.

## Run the DeepAgents backend

Follow `deepagents/README.md`. The runner requires a provider API key and a working DeepAgents installation. It writes the generated report and a session-matched `.runtime.json` record beside it. The record fingerprints the source case, generation-visible inputs, HarnessSpec, and report, and preserves the adapter's runtime capability/fidelity information.

## Compare the runtime forms

Run both forms on the same input and record model/runtime settings. Check report structure, source support, method coverage, explicit uncertainty, and architect review separately. Differences in agent delegation, state handling, or skill loading are fidelity findings; this example does not presume runtime equivalence.
