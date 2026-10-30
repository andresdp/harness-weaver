---
name: patterns-compatibility
description: Analyze compatibility, complementarity, conflicts, and dependencies among candidate architectural patterns.
---

# SKILL: Patterns Compatibility

## Objective

Determine which candidate patterns can be combined coherently and which
combinations may introduce conflicts or redundancies.

## Input Artifacts

Read:

/pattern_candidates.json

/requirements_analysis.json

/quality_attributes.json

/artifacts/drivers.json

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

/pattern_compatibility.json

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

Do not perform Alternative Generation.