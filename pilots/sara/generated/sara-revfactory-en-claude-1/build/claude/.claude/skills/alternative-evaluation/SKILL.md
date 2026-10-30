---
name: alternative-evaluation
description: SARA Stage 3, task 1. Evaluates every architecture alternative against each functional requirement, quality attribute and architectural driver using the scale satisfied / partially_satisfied / not_satisfied / unclear, with evidence, and writes alternative_evaluation.json. Used by the sara-alternative-evaluator agent inside the sara-orchestrator run; not for trade-offs or recommendations.
---

# Alternative Evaluation

Source: SARA `stage3-alternative_evaluation/skills/alternative-evaluation` (adapted paths only).

## Objective

Evaluate how well each alternative satisfies the requirements and architectural concerns identified in Stage 1.
Requirements are the primary evaluation criteria.

## Inputs

- `_workspace/artifacts/requirements_analysis.json`
- `_workspace/artifacts/quality_attributes.json`
- `_workspace/artifacts/drivers.json`
- `_workspace/artifacts/alternatives.json`

## Procedure

For every alternative evaluate:

- **Functional requirements** — for every requirement in `requirements_analysis.json`: satisfied, partially
  satisfied, or not satisfied.
- **Quality attributes** — the expected impact (`positive` | `neutral` | `negative` | `mixed` | `unclear`) on each
  relevant attribute.
- **Architectural drivers** — whether the alternative addresses each important driver.

Provide evidence and rationale for every evaluation.

## Evaluation scale

`satisfied`, `partially_satisfied`, `not_satisfied`, `unclear`. Do not assume satisfaction when evidence is
insufficient — use `unclear`, and each `unclear` becomes an unresolved gap in the stage register.

## Rules

- Requirements are primary; quality attributes and drivers complement them.
- Do not introduce new criteria without evidence. Do not perform trade-off analysis or recommend an alternative.
- Do not modify the alternatives or introduce new solutions.
- Cover every alternative × every requirement; reference requirements by ID and drivers by exact name.

## Output

Write `_workspace/artifacts/alternative_evaluation.json`:

```json
{
  "evaluations": [
    {
      "alternative_id": "A1",
      "requirement_evaluations": [
        { "requirement_id": "RF1", "status": "satisfied", "rationale": "...", "evidence": [] }
      ],
      "quality_attribute_evaluations": [
        { "quality_attribute": "...", "impact": "positive", "rationale": "...", "evidence": [] }
      ],
      "driver_evaluations": [
        { "driver": "...", "status": "satisfied", "rationale": "...", "evidence": [] }
      ]
    }
  ]
}
```

After writing, read the file back and verify it is valid JSON.
Do not perform Trade-off Analysis or Alternative Selection.
