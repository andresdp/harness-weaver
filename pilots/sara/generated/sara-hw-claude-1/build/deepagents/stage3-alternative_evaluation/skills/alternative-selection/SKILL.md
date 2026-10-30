---
name: alternative-selection
description: Select and recommend the most appropriate architectural alternative based on requirement satisfaction and trade-off analysis.
---

# SKILL: Alternative Selection

## Objective

Recommend the architectural alternative that best satisfies the requirements
and architectural drivers while considering the identified trade-offs.

## Input Artifacts

Read:

- /artifacts/alternatives.json
- /artifacts/alternative_evaluation.json
- /artifacts/trade_off_analysis.json

## Procedure

Determine the most appropriate alternative.

The recommendation must consider, in this order:

1. requirement satisfaction
2. architectural driver satisfaction
3. quality attribute impact
4. trade-offs
5. important limitations and risks

Explain why the selected alternative is preferable to the others.

## Rules

- Select exactly one recommended alternative.
- The recommendation must be supported by the evaluation and trade-off
  artifacts.
- Do not introduce a new alternative during selection.
- Do not change an existing alternative.
- Do not hide important weaknesses of the selected alternative.
- Do not generate the ADR yet.
- Do not generate the architecture diagram yet.

The selection is a recommendation based on the available evidence. It should
not claim empirical superiority when no empirical evaluation exists.

## Expected Output

Write:

/artifacts/alternative_selection.json

Structure:

```
{
  "selected_alternative_id": "A1",
  "selection_rationale": "...",
  "supporting_evidence": [],
  "key_advantages": [],
  "key_limitations": [],
  "rejected_alternatives": [
    {
      "alternative_id": "A2",
      "reason": "..."
    }
  ]
}
```

After writing the file, read it back and verify that it is valid JSON.

This is the final task of Stage 3.

<!-- HarnessWeaver: copied from SARA backend/app/agents/stage3-alternative_evaluation/skills/alternative-selection/SKILL.md @528ae7ce. Changed: artifact paths unified under /artifacts/ (harvest defect D3). Procedure, rules and structure unchanged. -->
