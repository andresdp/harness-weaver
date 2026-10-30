---
name: requirements-cross-analysis
description: "Analyze individual requirements and cross-requirement relationships, including ambiguities, dependencies, conflicts, overlaps, and inconsistencies. SARA Stage 1, task 1; executed only by the requirements-drivers-analyst agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/requirements-cross-analysis/SKILL.md (SARA @528ae7ce, sha256 1a05c0776a81cb63d0216ed4b73627384917300a31bdca8c81cbf135bf95d983). Adapted for the Claude Code bundle; see materialization-report.md. -->

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

_workspace/artifacts/requirements_analysis.json

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
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact requirements_analysis`

The contract is `references/requirements-analysis.schema.json`.

Do not perform Quality Attribute Identification or Driver Identification.