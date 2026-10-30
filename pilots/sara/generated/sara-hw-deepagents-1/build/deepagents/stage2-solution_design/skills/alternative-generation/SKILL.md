---
name: alternative-generation
description: Generate coherent and meaningfully different architectural alternatives from compatible pattern candidates.
---

# SKILL: Alternative Generation

## Objective

Generate a set of coherent architectural alternatives by combining compatible
pattern candidates in ways that address the architectural drivers.

## Input Artifacts

Read:

/artifacts/requirements_analysis.json

/artifacts/quality_attributes.json

/artifacts/drivers.json

/artifacts/pattern_candidates.json

/artifacts/pattern_compatibility.json

## Procedure

Generate multiple meaningful architectural alternatives.

For each alternative identify:

1. alternative_id
2. name
3. description
4. selected_patterns
5. addressed_drivers
6. rationale
7. assumptions
8. limitations

Alternatives should represent meaningful design choices rather than arbitrary
permutations of patterns.

## Rules

- Generate at least two distinct alternatives when the available evidence
  supports multiple solutions.
- Alternatives must be internally coherent.
- Use only compatible pattern combinations.
- Each alternative must address relevant architectural drivers.
- Alternatives must differ in meaningful architectural decisions.
- Do not evaluate alternatives yet.
- Do not select a preferred alternative.
- Do not perform trade-off analysis.
- Do not generate the final ADR.
- Do not create an architecture diagram.

The purpose of this task is exploration, not selection.

## Expected Output

Write:

/artifacts/alternatives.json

Structure:

```
{
  "alternatives": [
    {
      "alternative_id": "A1",
      "name": "...",
      "description": "...",
      "selected_patterns": [],
      "addressed_drivers": [],
      "rationale": "...",
      "assumptions": [],
      "limitations": []
    }
  ]
}
```

After writing the file, read it back and verify that it is valid JSON.

This is the final task of Stage 2.

<!-- HarnessWeaver: copied from SARA backend/app/agents/stage2-solution_design/skills/alternative-generation/SKILL.md @528ae7ce. Changed: artifact paths unified under /artifacts/ (harvest defect D3). Procedure, rules and structure unchanged. -->
