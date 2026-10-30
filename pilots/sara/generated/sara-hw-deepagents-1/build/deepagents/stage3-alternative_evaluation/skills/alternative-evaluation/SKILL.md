---
name: alternative-evaluation
description: Evaluate each architecture alternative against requirements, quality attributes, and architectural drivers.
---

# SKILL: Alternative Evaluation

## Objective

Evaluate how well each architectural alternative satisfies the requirements
and architectural concerns identified in Stage 1.

Requirements are the primary evaluation criteria.

## Input Artifacts

Read:

- /artifacts/requirements_analysis.json
- /artifacts/quality_attributes.json
- /artifacts/drivers.json
- /artifacts/alternatives.json

## Procedure

For every alternative evaluate:

### Functional requirements

Determine whether the alternative:

- satisfies the requirement
- partially satisfies the requirement
- does not satisfy the requirement

### Quality attributes

Determine the expected impact of the alternative on each relevant quality
attribute.

### Architectural drivers

Determine whether the alternative addresses each important driver.

For every evaluation provide evidence and rationale.

## Evaluation Scale

Use:

- satisfied
- partially_satisfied
- not_satisfied
- unclear

Do not assume satisfaction when the available evidence is insufficient.

## Rules

- Requirements are the primary satisfaction criteria.
- Quality attributes and drivers complement the requirements.
- Do not introduce new evaluation criteria without evidence.
- Do not perform trade-off analysis yet.
- Do not recommend an alternative.
- Do not modify the alternatives.
- Do not introduce new architectural solutions.

## Expected Output

Write:

/artifacts/alternative_evaluation.json

Structure:

```
{
  "evaluations": [
    {
      "alternative_id": "A1",
      "requirement_evaluations": [
        {
          "requirement_id": "RF1",
          "status": "satisfied",
          "rationale": "...",
          "evidence": []
        }
      ],
      "quality_attribute_evaluations": [
        {
          "quality_attribute": "...",
          "impact": "positive",
          "rationale": "...",
          "evidence": []
        }
      ],
      "driver_evaluations": [
        {
          "driver": "...",
          "status": "satisfied",
          "rationale": "...",
          "evidence": []
        }
      ]
    }
  ]
}
```

After writing the file, read it back and verify that it is valid JSON.

Do not perform Trade-off Analysis or Alternative Selection.

<!-- HarnessWeaver: copied from SARA backend/app/agents/stage3-alternative_evaluation/skills/alternative-evaluation/SKILL.md @528ae7ce. Changed: artifact paths unified under /artifacts/ (harvest defect D3). Procedure, rules and structure unchanged. -->
