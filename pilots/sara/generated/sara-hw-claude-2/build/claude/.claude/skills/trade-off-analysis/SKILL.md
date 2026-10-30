---
name: trade-off-analysis
description: "Analyze the trade-offs among architectural alternatives using the evaluation results and identify strengths, weaknesses, and tensions. SARA Stage 3, task 2; executed only by the alternative-evaluator agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/trade-off-analysis/SKILL.md (SARA @528ae7ce, sha256 d26d4ab57e55f8c8b01723edf5ed9dd41758b65cf1d66ce73ebb73b572255b80). Adapted for the Claude Code bundle; see materialization-report.md. -->

# SKILL: Trade-off Analysis

## Objective

Analyze the trade-offs between the architectural alternatives using the
evaluation results produced by the previous task.

## Input Artifacts

Read:

- _workspace/artifacts/requirements_analysis.json
- _workspace/artifacts/quality_attributes.json
- _workspace/artifacts/drivers.json
- _workspace/artifacts/alternatives.json
- _workspace/artifacts/alternative_evaluation.json

## Procedure

For each alternative identify:

1. major strengths
2. major weaknesses
3. quality attribute tensions
4. important architectural trade-offs
5. risks or costs when supported by evidence

## Rules

- Base the analysis on the previous evaluation.
- Do not repeat the entire evaluation.
- Do not invent empirical performance numbers.
- Do not claim quantitative superiority without evidence.
- Distinguish qualitative reasoning from measured evidence.
- Do not select the final alternative yet.

## Expected Output

Write:

_workspace/artifacts/trade_off_analysis.json

Structure:

```
{
  "trade_offs": [
    {
      "alternative_id": "A1",
      "strengths": [],
      "weaknesses": [],
      "qa_tensions": [],
      "arch_tradeoff": [],
      "risks": []
    }
  ]
}
```

After writing the file, read it back and verify that it is valid JSON.
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact trade_off_analysis`

The contract is `references/trade-off-analysis.schema.json`.

Do not perform Alternative Selection.