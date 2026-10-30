---
name: alternative-selection
description: SARA Stage 3, task 3 (final). Selects exactly one recommended architecture alternative from the evaluation and trade-off artifacts, with rationale, supporting evidence, advantages, limitations and per-alternative rejection reasons, and writes alternative_selection.json. Used by the sara-alternative-evaluator agent inside the sara-orchestrator run; not for writing the ADR or diagram.
---

# Alternative Selection

Source: SARA `stage3-alternative_evaluation/skills/alternative-selection` (adapted paths only).

## Objective

Recommend the alternative that best satisfies the requirements and drivers while considering the identified
trade-offs.

## Inputs

- `_workspace/artifacts/alternatives.json`
- `_workspace/artifacts/alternative_evaluation.json`
- `_workspace/artifacts/trade_off_analysis.json`

## Procedure

Determine the most appropriate alternative, considering in this order:

1. requirement satisfaction
2. architectural driver satisfaction
3. quality attribute impact
4. trade-offs
5. important limitations and risks

Explain why the selected alternative is preferable to each of the others.

## Rules

- Select exactly one alternative. Its ID must exist in `alternatives.json`.
- Support the recommendation with the evaluation and trade-off artifacts — cite them in `supporting_evidence`
  (for example `alternative_evaluation.json: A1/RF3 satisfied`).
- Do not introduce or change an alternative. Do not hide important weaknesses (`key_limitations` is never empty
  when the trade-off analysis lists weaknesses or risks for the selected alternative).
- Every non-selected alternative appears in `rejected_alternatives` with a reason.
- This is a recommendation based on available evidence; do not claim empirical superiority without empirical data.
- `selection_rationale` becomes the `selection_rationale` of the final package verbatim, so write it as a
  self-contained paragraph.
- Do not generate the ADR or diagram yet.

## Output

Write `_workspace/artifacts/alternative_selection.json`:

```json
{
  "selected_alternative_id": "A1",
  "selection_rationale": "...",
  "supporting_evidence": [],
  "key_advantages": [],
  "key_limitations": [],
  "rejected_alternatives": [
    { "alternative_id": "A2", "reason": "..." }
  ]
}
```

After writing, read the file back and verify it is valid JSON. This is the final SARA task of Stage 3.
