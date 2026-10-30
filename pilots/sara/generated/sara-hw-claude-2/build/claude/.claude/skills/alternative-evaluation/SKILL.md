---
name: alternative-evaluation
description: "Evaluate each architecture alternative against requirements, quality attributes, and architectural drivers. SARA Stage 3, task 1; executed only by the alternative-evaluator agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/alternative-evaluation/SKILL.md (SARA @528ae7ce, sha256 9602b37866aae2263f60bf03c1e5b43910ec0f3191a1dc46d83771dabc0a8d16). Adapted for the Claude Code bundle; see materialization-report.md. -->

# SKILL: Alternative Evaluation

## Objective

Evaluate how well each architectural alternative satisfies the requirements
and architectural concerns identified in Stage 1.

Requirements are the primary evaluation criteria.

## Input Artifacts

Read:

- _workspace/artifacts/requirements_analysis.json
- _workspace/artifacts/quality_attributes.json
- _workspace/artifacts/drivers.json
- _workspace/artifacts/alternatives.json

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

_workspace/artifacts/alternative_evaluation.json

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
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact alternative_evaluation`

The contract is `references/alternative-evaluation.schema.json`.

Do not perform Trade-off Analysis or Alternative Selection.