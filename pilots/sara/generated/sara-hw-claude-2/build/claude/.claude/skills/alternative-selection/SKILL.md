---
name: alternative-selection
description: "Select and recommend the most appropriate architectural alternative based on requirement satisfaction and trade-off analysis. SARA Stage 3, task 3; executed only by the alternative-evaluator agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/alternative-selection/SKILL.md (SARA @528ae7ce, sha256 65f9996eb602bd1bbc160f30489cdf598f9a43e286c61b91fd02f30e6f0b78c8). Adapted for the Claude Code bundle; see materialization-report.md. -->

# SKILL: Alternative Selection

## Objective

Recommend the architectural alternative that best satisfies the requirements
and architectural drivers while considering the identified trade-offs.

## Input Artifacts

Read:

- _workspace/artifacts/alternatives.json
- _workspace/artifacts/alternative_evaluation.json
- _workspace/artifacts/trade_off_analysis.json

## Procedure

Determine the most appropriate alternative.

The recommendation must consider, in this order:

1. requirement satisfaction
2. architectural driver satisfaction
3. quality attribute impact
4. trade-offs
5. important limitations and risks

Explain why the selected alternative is preferable to the others.

## Rules

- Select exactly one recommended alternative.
- The recommendation must be supported by the evaluation and trade-off
  artifacts.
- Do not introduce a new alternative during selection.
- Do not change an existing alternative.
- Do not hide important weaknesses of the selected alternative.
- Do not generate the ADR yet.
- Do not generate the architecture diagram yet.

The selection is a recommendation based on the available evidence. It should
not claim empirical superiority when no empirical evaluation exists.

## Expected Output

Write:

_workspace/artifacts/alternative_selection.json

Structure:

```
{
  "selected_alternative_id": "A1",
  "selection_rationale": "...",
  "supporting_evidence": [],
  "key_advantages": [],
  "key_limitations": [],
  "rejected_alternatives": [
    {
      "alternative_id": "A2",
      "reason": "..."
    }
  ]
}
```

After writing the file, read it back and verify that it is valid JSON.
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact alternative_selection`

The contract is `references/alternative-selection.schema.json`.

This is the final task of Stage 3.