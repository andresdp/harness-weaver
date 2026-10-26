# ATAM evaluation harness (Claude Code bundle)

This harness produces an evidence-grounded ATAM evaluation **draft** of a supplied architecture for a software architect
to review. It doesn't run stakeholder workshops, invent priorities or measurements, or replace expert review.

## Requirements
- Claude Code CLI (`claude`) on PATH, authenticated
- Python 3.9+ with `jsonschema` (`pip install jsonschema`)

## Run
From this directory:

```shell
python3 atam_harness/run.py --input /path/to/evaluation_inputs.json      # new run
python3 atam_harness/run.py --from stage4-analyze_scenarios              # redo a stage and everything after it
python3 atam_harness/run.py --resume                                     # continue an interrupted run
python3 atam_harness/run.py --input case.json --dry-run                  # show the plan
python3 atam_harness/atam.py status                                      # ledger summary
```

Inside an interactive Claude Code session, ask it to "evaluate this architecture with ATAM" and the
`atam-orchestrator` skill will drive the same runner.

The input is template-shaped JSON (`ATAM_Evaluation.evaluation_inputs`, plus optional `title` and `metadata`); see
`.claude/skills/evaluate-architecture/references/atam-report-template.json`. Input containing `ground_truth_outputs` is refused.

## Stages and outputs (`_workspace/`)

| Stage | Writes only |
| --- | --- |
| stage0-intake (deterministic) | 00_evaluation_inputs.json |
| stage1-establish_context | 01_context.json |
| stage2-build_utility_tree | 02_utility_tree.json |
| stage3-identify_approaches | 03_approaches.json |
| stage4-analyze_scenarios | 04_analysis.json |
| stage5-synthesize_report | 05_atam_report_draft.json |
| stage6-check_evaluation | 06_review_findings_initial.json |
| stage7-revise_report | 05_atam_report.json, 06_review_findings.json |

The final report is `05_atam_report.json`, which conforms to `atam-report.schema.json` and keeps `report_status: draft`.
Final readiness is `06_review_findings.json → ready_for_architect_review`. Stage 7 computes it in code, and it stays
false while any warn or fail remains. `run_ledger.json` records the order and the output hashes of every stage, and
`.runtime/` holds the per-stage logs.

## Self-tests
```shell
python3 -m unittest discover -s atam_harness/tests -v
```
They use a fake `claude` and a placeholder fixture that is not case data.
