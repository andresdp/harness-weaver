---
name: alternative-generation
description: SARA Stage 2, task 3 (final). Generates coherent, meaningfully different architecture alternatives from compatible pattern candidates, each with addressed drivers, rationale, assumptions and limitations, and writes alternatives.json. Used by the sara-solution-designer agent inside the sara-orchestrator run; not for evaluating or selecting alternatives.
---

# Alternative Generation

Source: SARA `stage2-solution_design/skills/alternative-generation` (adapted paths only).

## Objective

Generate a set of coherent architectural alternatives by combining compatible pattern candidates in ways that
address the architectural drivers. The purpose is exploration, not selection.

## Inputs

- `_workspace/artifacts/requirements_analysis.json`
- `_workspace/artifacts/quality_attributes.json`
- `_workspace/artifacts/drivers.json`
- `_workspace/artifacts/pattern_candidates.json`
- `_workspace/artifacts/pattern_compatibility.json`

## Procedure

Generate multiple meaningful alternatives. For each identify: `alternative_id`, `name`, `description`,
`selected_patterns`, `addressed_drivers`, `rationale`, `assumptions`, `limitations`.

Alternatives represent meaningful design choices, not arbitrary permutations of patterns.

## Rules

- Generate at least two distinct alternatives when the evidence supports multiple solutions. If it supports only
  one, generate one and record why in the stage gap register.
- Alternatives must be internally coherent and use only combinations supported by `pattern_compatibility.json`.
- Each alternative addresses relevant drivers (`addressed_drivers` uses exact driver names) and differs from the
  others in meaningful architectural decisions.
- `assumptions` lists only what the alternative relies on that the inputs do not state. These feed the final
  assumptions register, so state each one as a checkable sentence.
- Use IDs `A1`, `A2`, ... — Stage 3 and the final package reference them.
- Do not evaluate, select, perform trade-off analysis, write the ADR or draw a diagram.

## Output

Write `_workspace/artifacts/alternatives.json`:

```json
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

After writing, read the file back and verify it is valid JSON. This is the final SARA task of Stage 2.
