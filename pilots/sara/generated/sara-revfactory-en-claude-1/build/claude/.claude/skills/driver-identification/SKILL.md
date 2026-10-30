---
name: driver-identification
description: SARA Stage 1, task 3 (final). Identifies and prioritizes the architectural drivers — requirements, quality attributes, constraints and concerns with the strongest architectural influence — and writes drivers.json. Used by the sara-requirements-analyst agent inside the sara-orchestrator run; not for proposing solutions.
---

# Driver Identification

Source: SARA `stage1-requirements_drivers/skills/driver-identification` (adapted paths only).

## Objective

Identify the main architectural drivers that will guide exploration (Stage 2) and evaluation (Stage 3).

## Inputs

- `_workspace/artifacts/requirements_analysis.json`
- `_workspace/artifacts/quality_attributes.json`

## Procedure

Identify the requirements, quality attributes, constraints and concerns that most strongly influence architectural
design. For each driver identify: `name`, `description`, `driver_type`, `priority`, `source_requirement_ids`,
`supporting_evidence`.

`driver_type` is one of: `functional_requirement`, `quality_attribute`, `constraint`, `integration_concern`,
`business_concern`, `technical_concern`.

## Rules

- Drivers must be supported by evidence. Prioritize by architectural significance (`high` | `medium` | `low`).
- Do not propose solutions, patterns, tactics or technologies. Do not select an architecture.
- Do not turn a preferred solution into a driver. A driver describes WHAT influences design, not HOW.
  Correct: "Support for mobile and PC clients through HTTP/REST is an architectural driver."
  Incorrect: "Use an API Gateway."
- Give each driver a short, unique `name`; later stages reference drivers by this exact string.
- A constraint stated in the input (for example a mandated protocol) is a legitimate `constraint` driver; a
  technology you would merely prefer is not.

## Output

Write `_workspace/artifacts/drivers.json`:

```json
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

After writing, read the file back and verify it is valid JSON. This is the final SARA task of Stage 1
(the harness then asks you to write the stage gap register).
