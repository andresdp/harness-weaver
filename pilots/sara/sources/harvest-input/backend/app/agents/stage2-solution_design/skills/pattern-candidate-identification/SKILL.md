---
name: pattern-candidate-identification
description: Identify architectural pattern candidates that may address the requirements and architectural drivers.
---

# SKILL: Pattern Candidate Identification

## Objective

Identify architectural pattern candidates that could potentially address the
architectural drivers and relevant requirements.

## Input Artifacts

Read:

/requirements_analysis.json

/quality_attributes.json

/drivers.json

## Procedure

For each relevant architectural concern:

1. Identify candidate architectural patterns.
2. Explain what concern each pattern addresses.
3. Identify the requirements or drivers supporting the candidate.
4. Explain why the pattern is potentially relevant.
5. Identify important limitations or concerns.

## Rules

- Generate candidates, not final solutions.
- Do not select a single pattern as the final architecture.
- Do not assume that a pattern is appropriate merely because it is popular.
- Candidates must be justified by requirements or drivers.
- Do not invent pattern definitions.
- Do not introduce implementation details unless necessary to distinguish
  candidates.
- Preserve multiple plausible candidates when the evidence supports them.

## Expected Output

Write:

/pattern_candidates.json

Structure:

```
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

After writing the file, read it back and verify that it is valid JSON.

Do not perform compatibility analysis or alternative generation.