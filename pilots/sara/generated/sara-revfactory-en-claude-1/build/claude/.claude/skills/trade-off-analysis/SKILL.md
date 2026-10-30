---
name: trade-off-analysis
description: SARA Stage 3, task 2. Analyzes trade-offs among the evaluated architecture alternatives — strengths, weaknesses, quality-attribute tensions, architectural trade-offs and evidence-backed risks — and writes trade_off_analysis.json. Used by the sara-alternative-evaluator agent inside the sara-orchestrator run; not for selecting the final alternative.
---

# Trade-off Analysis

Source: SARA `stage3-alternative_evaluation/skills/trade-off-analysis` (adapted paths only).

## Objective

Analyze the trade-offs between the alternatives using the evaluation results of the previous task.

## Inputs

- `_workspace/artifacts/requirements_analysis.json`
- `_workspace/artifacts/quality_attributes.json`
- `_workspace/artifacts/drivers.json`
- `_workspace/artifacts/alternatives.json`
- `_workspace/artifacts/alternative_evaluation.json`

## Procedure

For each alternative identify: major strengths, major weaknesses, quality-attribute tensions, important
architectural trade-offs, and risks or costs when supported by evidence.

## Rules

- Base the analysis on the previous evaluation; do not repeat the entire evaluation.
- Do not invent empirical performance numbers or claim quantitative superiority without evidence.
- Distinguish qualitative reasoning from measured evidence (mark qualitative statements as such when ambiguous).
- Do not select the final alternative yet.
- Include an entry for every `alternative_id` in `alternatives.json`.

## Output

Write `_workspace/artifacts/trade_off_analysis.json`:

```json
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

After writing, read the file back and verify it is valid JSON. Do not perform Alternative Selection.
