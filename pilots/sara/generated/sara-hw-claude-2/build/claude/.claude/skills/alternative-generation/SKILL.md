---
name: alternative-generation
description: "Generate coherent and meaningfully different architectural alternatives from compatible pattern candidates. SARA Stage 2, task 3; executed only by the solution-designer agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/alternative-generation/SKILL.md (SARA @528ae7ce, sha256 bb462603a08b5f70002672c68fcf245295ca700379f3988fe355f1cf3fda65e3). Adapted for the Claude Code bundle; see materialization-report.md. -->

# SKILL: Alternative Generation

## Objective

Generate a set of coherent architectural alternatives by combining compatible
pattern candidates in ways that address the architectural drivers.

## Input Artifacts

Read:

_workspace/artifacts/requirements_analysis.json

_workspace/artifacts/quality_attributes.json

_workspace/artifacts/drivers.json

_workspace/artifacts/pattern_candidates.json

_workspace/artifacts/pattern_compatibility.json

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

_workspace/artifacts/alternatives.json

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
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact alternatives`

The contract is `references/alternatives.schema.json`.

This is the final task of Stage 2.