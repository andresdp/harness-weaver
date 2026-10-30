---
name: assumptions-gap-register
description: Harness addition used at the end of every SARA stage. Records the stage's ambiguities, assumptions, inferences, unresolved gaps and process notes — each traced to its origin artifact and requirement IDs — in stageN_assumptions_gaps.json, without resolving or inventing anything. Used by the four SARA stage agents inside the sara-orchestrator run; not a substitute for the SARA task artifacts.
---

# Assumptions & Gap Register

## Why this exists

SARA forbids resolving ambiguities by inventing assumptions, but its artifacts scatter open questions across
`ambiguities`, `assumptions`, `unclear` evaluations and limitations. The final contract has no field for them.
This register collects them per stage so the ADR and the final package can state, traceably, what the decision
rests on and what is still open. It **records**; it never resolves, prioritizes away, or adds requirements.

## When to run

As the last task of each stage, after all SARA task artifacts of that stage are written and verified.
Write `_workspace/artifacts/stage{N}_assumptions_gaps.json` (N = 1..4). Always write the file, even if empty.

## What to record (by stage)

| Stage | Harvest from | Typical `kind` |
|-------|--------------|----------------|
| 1 | every `ambiguities` entry; conflicts/inconsistencies in `cross_requirement_relationships`; `Inferred:` behaviors that drivers rely on; strongly-implied quality attributes; ID labeling done by the harness | `ambiguity`, `inference`, `unresolved_gap`, `process_note` |
| 2 | each alternative's `assumptions`; conditions in `pattern_compatibility.json` that the inputs cannot confirm; evidence that only supports one alternative | `assumption`, `unresolved_gap` |
| 3 | every `unclear` or `not_satisfied` evaluation of the **selected** alternative; risks lacking measured evidence; problems found in earlier artifacts | `unresolved_gap`, `assumption` |
| 4 | anything the ADR or diagram had to leave abstract because inputs were silent (for example a communication mechanism not stated) | `unresolved_gap`, `process_note` |

Carry forward an earlier-stage entry only by referencing its ID in `related_ids`; do not duplicate it.

## Rules

- Quote or point to the origin: `origin` is `artifact.json#/json/pointer` (or `input:functional_requirements` for raw input).
- `source_refs` lists requirement IDs, driver names or alternative IDs the entry concerns.
- `status`: `open` (needs stakeholder input), `relied_upon` (an alternative or the decision depends on it),
  `noted` (informational, no action needed).
- `resolution_needed`: the concrete question a stakeholder would have to answer; empty for `noted`.
- IDs are `S{N}-G{k}`, unique and stable across re-runs of the same stage where the entry is unchanged.
- Do not invent entries to look thorough; an empty `entries` array is valid.

## Output

```json
{
  "stage": 1,
  "entries": [
    {
      "id": "S1-G1",
      "kind": "ambiguity",
      "statement": "...",
      "origin": "requirements_analysis.json#/requirements/2/ambiguities/0",
      "source_refs": ["RF3"],
      "related_ids": [],
      "status": "open",
      "resolution_needed": "..."
    }
  ]
}
```

`kind` is one of `ambiguity`, `assumption`, `inference`, `unresolved_gap`, `process_note`.
Read the file back and verify it is valid JSON.
