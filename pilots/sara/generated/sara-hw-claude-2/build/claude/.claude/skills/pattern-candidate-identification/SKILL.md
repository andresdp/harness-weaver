---
name: pattern-candidate-identification
description: "Identify architectural pattern candidates that may address the requirements and architectural drivers. SARA Stage 2, task 1; executed only by the solution-designer agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/pattern-candidate-identification/SKILL.md (SARA @528ae7ce, sha256 0a57b8daf9591a69e870ca3687227cce6dd2b828505483fb6529a05c214d1d58). Adapted for the Claude Code bundle; see materialization-report.md. -->

# SKILL: Pattern Candidate Identification

## Objective

Identify architectural pattern candidates that could potentially address the
architectural drivers and relevant requirements.

## Input Artifacts

Read:

_workspace/artifacts/requirements_analysis.json

_workspace/artifacts/quality_attributes.json

_workspace/artifacts/drivers.json

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

_workspace/artifacts/pattern_candidates.json

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
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact pattern_candidates`

The contract is `references/pattern-candidates.schema.json`.

Do not perform compatibility analysis or alternative generation.