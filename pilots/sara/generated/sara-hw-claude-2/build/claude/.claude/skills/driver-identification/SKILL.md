---
name: driver-identification
description: "Identify and prioritize the architectural drivers that will influence solution design. SARA Stage 1, task 3; executed only by the requirements-drivers-analyst agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/driver-identification/SKILL.md (SARA @528ae7ce, sha256 1d1f710a9d7b695f60e6ac6c3788e8cf72b86515d5123b32c946adf72274c6f1). Adapted for the Claude Code bundle; see materialization-report.md. -->

# SKILL: Driver Identification

## Objective

Identify the main architectural drivers that will guide the exploration and
evaluation of architectural solutions in subsequent stages.

## Input Artifacts

Read:

- _workspace/artifacts/requirements_analysis.json
- _workspace/artifacts/quality_attributes.json

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

_workspace/artifacts/drivers.json

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
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact drivers`

The contract is `references/drivers.schema.json`.

This is the final task of Stage 1.