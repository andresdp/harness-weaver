---
name: requirements-cross-analysis
description: Analyze individual requirements and cross-requirement relationships, including ambiguities, dependencies, conflicts, overlaps, and inconsistencies.
---

# SKILL: Requirements & Cross-Requirement Analysis

## Objective

Analyze the requirements individually and collectively to establish a precise
understanding of the problem domain before architectural design begins.

## Procedure

For each requirement identify:

1. requirement_id
2. requirement_description
3. implicit_behaviors
4. ambiguities

Then analyze relationships between requirements and identify:

1. dependencies
2. overlaps
3. conflicts
4. shared concerns
5. inconsistencies
6. relationships involving shared data or functionality

## Rules

- Preserve the original intent of the requirements.
- Do not invent missing business rules.
- Do not introduce architectural solutions.
- Do not infer technologies.
- Do not infer architectural patterns.
- Clearly distinguish explicit information from inference.
- Only identify ambiguities when there is insufficient or unclear information.
- Do not resolve ambiguities by inventing assumptions.
- Relationships between requirements must be supported by evidence from the
  requirements or project description.

## Expected Output

The output MUST be written as JSON to:

/requirements_analysis.json

The JSON must have this structure:

```
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

After writing the file, read it back and verify that it is valid JSON.

Do not perform Quality Attribute Identification or Driver Identification.