---
name: patterns-compatibility
description: "Analyze compatibility, complementarity, conflicts, and dependencies among candidate architectural patterns. SARA Stage 2, task 2; executed only by the solution-designer agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/patterns-compatibility/SKILL.md (SARA @528ae7ce, sha256 8e68b3f2b7cb0638300f4476fe47f310fd97024ac88bf112cafe5b64c19fefe2). Adapted for the Claude Code bundle; see materialization-report.md. -->

# SKILL: Patterns Compatibility

## Objective

Determine which candidate patterns can be combined coherently and which
combinations may introduce conflicts or redundancies.

## Input Artifacts

Read:

_workspace/artifacts/pattern_candidates.json

_workspace/artifacts/requirements_analysis.json

_workspace/artifacts/quality_attributes.json

_workspace/artifacts/drivers.json

## Procedure

For relevant pairs or groups of patterns determine:

1. compatibility
2. complementarity
3. conflict
4. redundancy
5. dependency
6. conditions required for combination

The analysis must explain WHY two patterns are compatible or incompatible.

## Rules

- Do not assume that all patterns can be combined.
- Do not assume that incompatible patterns are always mutually exclusive;
  identify conditions when appropriate.
- Do not generate complete architecture alternatives yet.
- Do not select a final solution.
- Do not introduce patterns that were not identified as candidates unless
  strictly necessary; if one is introduced, explain the evidence.
- Compatibility must be analyzed in relation to the requirements and drivers.

## Expected Output

Write:

_workspace/artifacts/pattern_compatibility.json

Structure:

```
{
  "compatibility_analysis": [
    {
      "patterns": ["Pattern A", "Pattern B"],
      "relationship": "compatible",
      "rationale": "...",
      "conditions": [],
      "affected_drivers": []
    }
  ]
}
```

After writing the file, read it back and verify that it is valid JSON.
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact pattern_compatibility`

The contract is `references/pattern-compatibility.schema.json`.

Do not perform Alternative Generation.