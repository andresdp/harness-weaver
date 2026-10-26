# ATAM evaluation harness: DeepAgents stage pipeline

Generated from HarnessSpec `archeval-atam-harness` (`../../harnessspec.yaml`, spec_version 0.2) for the HarnessWeaver stage host.

## What it does

Produces an evidence-grounded ATAM evaluation **draft** (`05_atam_report.json`, conforming to `contracts/atam-report.schema.json`) and a review record (`06_review_findings.json`) from one case input. A software architect familiar with the evaluated system must review the draft before it informs any decision (human gate `H1-architect-review`). This pipeline does not simulate stakeholder workshops.

## Running

The host reads `wiring.yaml`. It writes the case input (port `evaluation_inputs`) to `/artifacts/00_evaluation_inputs.json`, then runs stages 1–5 in order. Each stage gets its own deep agent, which mounts the stage directory at `/agent/` (`AGENTS.md` as memory, `skills/` as skills). After each stage, the host checks the listed artifacts and validates them against the named schemas.

- Model: `openai:gpt-5.4-mini` (single env-driven model, gate G5).
- Human-in-the-loop: none in the pipeline. The H1 gate is recorded in `wiring.yaml` for the host to report; the host does not approve it.
- Subagents: not used.

Supply an input that holds only `evaluation_inputs` (plus optional `metadata`/`title`), optionally wrapped in `ATAM_Evaluation`. If it contains `ground_truth_outputs` or `evaluation_results`, stage 1 stops without writing an artifact.

## Layout

```
wiring.yaml                      host contract
contracts/*.schema.json          artifact contracts (atam-report.schema.json is the supplied report contract)
stage1-establish_context/        → 01_context.json
stage2-build_utility_tree/       → 02_utility_tree.json
stage3-identify_approaches/      → 03_approaches.json
stage4-analyze_scenarios/        → 04_analysis.json
stage5-synthesize_and_review/    → 05_atam_report.json, 06_review_findings.json
materialization-report.md        fidelity record
```

## Maintenance

Trigger-condition validation does not apply at runtime (skills are invoked in the order `AGENTS.md` pins). When editing skill descriptions, keep them specific so that maintainers and `evolve` can tell the tasks apart.

## Change history

| Date | Change | Target | Reason |
|---|---|---|---|
| 2026-10-25 | Initial materialization from HarnessSpec `archeval-atam-harness` 0.2 | all stages | Fresh build |
