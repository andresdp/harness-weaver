---
name: quality-attribute-identification
description: "Identify quality attributes supported by the requirements and their interactions. SARA Stage 1, task 2; executed only by the requirements-drivers-analyst agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/quality-attribute-identification/SKILL.md (SARA @528ae7ce, sha256 db5c1c8dfed5a6a9b5b459b6e828ced628bed6d191db9163c6adaacf65b1b0a9). Adapted for the Claude Code bundle; see materialization-report.md. -->

# SKILL: Quality Attribute Identification

## Objective

Identify the quality attributes that are relevant to the system based on
explicit or strongly implied evidence in the requirements.

## Input Artifacts

Read:

_workspace/artifacts/requirements_analysis.json

## Procedure

Identify quality attributes relevant to the project.

For each quality attribute determine:

1. name
2. description
3. rationale
4. source_requirement_ids
5. evidence
6. priority

Consider attributes such as:

- performance
- scalability
- availability
- reliability
- security
- modifiability
- interoperability
- usability
- maintainability

Only include attributes supported by evidence.

## Rules

- Prefer explicit evidence from the requirements.
- Strongly implied quality attributes may be included when justified.
- Do not invent quality attributes merely because they are common architectural
  concerns.
- Do not propose tactics.
- Do not propose patterns.
- Do not propose technologies.
- Do not propose architecture styles.
- Do not make final architectural decisions.
- Do not confuse a quality attribute with a solution.

For example:

Correct:
"Interoperability is relevant because the system must expose functionality
through HTTP/REST."

Incorrect:
"The system should use an API Gateway."

The first identifies a quality concern; the second proposes a solution.

## Expected Output

Write the result to:

_workspace/artifacts/quality_attributes.json

Structure:

```
{
  "quality_attributes": [
    {
      "name": "...",
      "description": "...",
      "rationale": "...",
      "source_requirement_ids": [],
      "evidence": [],
      "priority": "high"
    }
  ]
}
```

After writing the file, read it back and verify that it is valid JSON.
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact quality_attributes`

The contract is `references/quality-attributes.schema.json`.

Do not perform Driver Identification.