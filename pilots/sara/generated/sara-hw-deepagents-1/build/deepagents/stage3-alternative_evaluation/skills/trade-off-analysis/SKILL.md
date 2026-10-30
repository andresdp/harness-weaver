---
name: trade-off-analysis
description: Analyze the trade-offs among architectural alternatives using the evaluation results and identify strengths, weaknesses, and tensions.
---

# SKILL: Trade-off Analysis

## Objective

Analyze the trade-offs between the architectural alternatives using the
evaluation results produced by the previous task.

## Input Artifacts

Read:

- /artifacts/requirements_analysis.json
- /artifacts/quality_attributes.json
- /artifacts/drivers.json
- /artifacts/alternatives.json
- /artifacts/alternative_evaluation.json

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

/artifacts/trade_off_analysis.json

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

Do not perform Alternative Selection.

<!-- HarnessWeaver: copied from SARA backend/app/agents/stage3-alternative_evaluation/skills/trade-off-analysis/SKILL.md @528ae7ce. Changed: artifact paths unified under /artifacts/ (harvest defect D3). Procedure, rules and structure unchanged. -->
