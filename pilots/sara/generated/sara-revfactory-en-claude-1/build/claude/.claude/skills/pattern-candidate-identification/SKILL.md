---
name: pattern-candidate-identification
description: SARA Stage 2, task 1. Identifies architectural pattern candidates that may address the Stage 1 drivers and requirements, with the concerns each addresses, supporting evidence and limitations, and writes pattern_candidates.json. Used by the sara-solution-designer agent inside the sara-orchestrator run; not for selecting a final architecture.
---

# Pattern Candidate Identification

Source: SARA `stage2-solution_design/skills/pattern-candidate-identification` (adapted paths only).

## Objective

Identify architectural pattern candidates that could potentially address the architectural drivers and relevant
requirements.

## Inputs

- `_workspace/artifacts/requirements_analysis.json`
- `_workspace/artifacts/quality_attributes.json`
- `_workspace/artifacts/drivers.json`

## Procedure

For each relevant architectural concern:

1. Identify candidate architectural patterns.
2. Explain what concern each pattern addresses.
3. Identify the requirements or drivers supporting the candidate.
4. Explain why the pattern is potentially relevant.
5. Identify important limitations or concerns.

## Rules

- Generate candidates, not final solutions. Do not select a single pattern as the final architecture.
- Do not assume a pattern is appropriate because it is popular; candidates must be justified by requirements or
  drivers.
- Do not invent pattern definitions — use established, recognizable pattern names and meanings.
- Do not introduce implementation details unless needed to distinguish candidates.
- Preserve multiple plausible candidates when the evidence supports them.
- `source_requirement_ids` must exist in `requirements_analysis.json`; `source_driver_names` must match
  `drivers.json` names exactly.

## Output

Write `_workspace/artifacts/pattern_candidates.json`:

```json
{
  "pattern_candidates": [
    {
      "pattern_name": "...",
      "description": "...",
      "addressed_concerns": [],
      "source_requirement_ids": [],
      "source_driver_names": [],
      "rationale": "...",
      "limitations": []
    }
  ]
}
```

After writing, read the file back and verify it is valid JSON.
Do not perform compatibility analysis or alternative generation.
