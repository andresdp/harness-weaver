---
name: patterns-compatibility
description: SARA Stage 2, task 2. Analyzes compatibility, complementarity, conflict, redundancy and dependency among the identified pattern candidates, with the conditions required to combine them, and writes pattern_compatibility.json. Used by the sara-solution-designer agent inside the sara-orchestrator run; not for generating complete alternatives.
---

# Patterns Compatibility

Source: SARA `stage2-solution_design/skills/patterns-compatibility` (adapted paths; the source's mixed
`/artifacts/drivers.json` vs `/drivers.json` reference is normalized).

## Objective

Determine which candidate patterns can be combined coherently and which combinations may introduce conflicts or
redundancies. Alternative Generation may only use combinations this analysis supports.

## Inputs

- `_workspace/artifacts/pattern_candidates.json`
- `_workspace/artifacts/requirements_analysis.json`
- `_workspace/artifacts/quality_attributes.json`
- `_workspace/artifacts/drivers.json`

## Procedure

For relevant pairs or groups of patterns determine: compatibility, complementarity, conflict, redundancy,
dependency, and conditions required for combination. Explain WHY patterns are compatible or incompatible.

`relationship` is one of: `compatible`, `complementary`, `conflicting`, `redundant`, `dependent`,
`conditionally_compatible`.

## Rules

- Do not assume all patterns can be combined.
- Do not assume incompatible patterns are always mutually exclusive; identify conditions when appropriate.
- Do not generate complete alternatives yet. Do not select a final solution.
- Do not introduce patterns that were not candidates unless strictly necessary; if you do, explain the evidence.
- Analyze compatibility in relation to the requirements and drivers; `affected_drivers` uses exact driver names.
- Every name in `patterns` must match a `pattern_name` in `pattern_candidates.json` (or be a justified addition).

## Output

Write `_workspace/artifacts/pattern_compatibility.json`:

```json
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

After writing, read the file back and verify it is valid JSON. Do not perform Alternative Generation.
