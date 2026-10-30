---
name: requirements-cross-analysis
description: SARA Stage 1, task 1. Analyzes each functional requirement (implicit behaviors, ambiguities) and the relationships between requirements (dependencies, overlaps, conflicts, shared concerns, inconsistencies) and writes requirements_analysis.json. Used by the sara-requirements-analyst agent inside the sara-orchestrator run; not for general requirements writing or for proposing solutions.
---

# Requirements & Cross-Requirement Analysis

Source: SARA `stage1-requirements_drivers/skills/requirements-cross-analysis` (adapted paths only).

## Objective

Establish a precise understanding of the problem domain by analyzing requirements individually and collectively,
before any architectural design begins. Every later stage traces back to the IDs and evidence fixed here, so
precision matters more than coverage.

## Inputs

- `_workspace/00_input/project_description.md`
- `_workspace/00_input/functional_requirements.md`

## Procedure

1. For each requirement identify: `requirement_id`, `requirement_description`, `implicit_behaviors`, `ambiguities`.
2. Then analyze relationships between requirements and identify: dependencies, overlaps, conflicts, shared concerns,
   inconsistencies, and relationships involving shared data or functionality.

## Rules

- Preserve the original intent of the requirements; keep given IDs. (If none are given, label `RF1..RFn` in input
  order and note it in the stage gap register.)
- Do not invent missing business rules. Do not introduce architectural solutions, technologies or patterns.
- Clearly distinguish explicit information from inference — prefix inferred implicit behaviors with `Inferred:`.
- Identify ambiguities only when information is insufficient or unclear, and do not resolve them by inventing
  assumptions. Unresolved ambiguities are carried into the gap register, which is how they stay visible.
- Relationships must be supported by evidence quoted or paraphrased from the requirements or project description.
- Use `relationship_type` values: `dependency`, `overlap`, `conflict`, `shared_concern`, `inconsistency`,
  `shared_data`, `shared_functionality`.

## Output

Write `_workspace/artifacts/requirements_analysis.json`:

```json
{
  "requirements": [
    {
      "requirement_id": "RF1",
      "requirement_description": "...",
      "implicit_behaviors": [],
      "ambiguities": []
    }
  ],
  "cross_requirement_relationships": [
    {
      "requirement_ids": ["RF1", "RF2"],
      "relationship_type": "dependency",
      "description": "...",
      "evidence": []
    }
  ]
}
```

After writing, read the file back and verify it is valid JSON.
Do not perform Quality Attribute Identification or Driver Identification.
