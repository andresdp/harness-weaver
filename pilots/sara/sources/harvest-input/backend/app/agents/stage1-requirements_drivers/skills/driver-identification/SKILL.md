---
name: driver-identification
description: Identify and prioritize the architectural drivers that will influence solution design.
---

# SKILL: Driver Identification

## Objective

Identify the main architectural drivers that will guide the exploration and
evaluation of architectural solutions in subsequent stages.

## Input Artifacts

Read:

- /requirements_analysis.json
- /quality_attributes.json

## Procedure

Identify the requirements, quality attributes, constraints, and concerns that
have the strongest influence on architectural design.

For each driver identify:

1. name
2. description
3. driver_type
4. priority
5. source_requirement_ids
6. supporting_evidence

Possible driver types include:

- functional_requirement
- quality_attribute
- constraint
- integration_concern
- business_concern
- technical_concern

## Rules

- Drivers must be supported by evidence.
- Prioritize drivers according to their architectural significance.
- Do not propose solutions.
- Do not propose patterns.
- Do not propose tactics.
- Do not propose technologies.
- Do not select an architecture.
- Do not transform a preferred solution into a driver.

A driver describes WHAT influences architectural design, not HOW the system
should be designed.

For example:

Correct:
"Support for mobile and PC clients through HTTP/REST is an architectural
driver."

Incorrect:
"Use an API Gateway."

## Expected Output

Write:

/drivers.json

Structure:

```
{
  "drivers": [
    {
      "name": "...",
      "description": "...",
      "driver_type": "...",
      "priority": "high",
      "source_requirement_ids": [],
      "supporting_evidence": []
    }
  ]
}
```

After writing the file, read it back and verify that it is valid JSON.

This is the final task of Stage 1.