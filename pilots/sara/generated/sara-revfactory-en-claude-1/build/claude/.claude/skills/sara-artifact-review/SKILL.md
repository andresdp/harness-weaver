---
name: sara-artifact-review
description: Checklist for reviewing SARA stage artifacts and the final architecture decision package — existence, JSON validity, declared shapes, cross-artifact ID consistency, stage boundary rules, and the output contract. Used by the sara-contract-reviewer agent after each stage of the sara-orchestrator run; not for reviewing source code or arbitrary documents.
---

# SARA Artifact Review

Declared shapes live in `references/`:

- `references/sara-stage-artifacts.schema.json` — one `$defs` entry per intermediate artifact and the gap register.
- `references/architecture-decision.schema.json` — the required final output contract (copied unchanged from the
  pilot source; it is authoritative).

The schemas are declarative references. No custom validator exists in this harness; you apply them by reading
(or with an off-the-shelf CLI if one is installed). Findings that depend on judgment must quote evidence.

## Common checks (every stage)

1. Every expected artifact exists under `_workspace/artifacts/` (see the table below).
2. Each `.json` parses (`python3 -m json.tool` / `jq empty`, else by reading).
3. Required keys and enum values match the `$defs` entry. Arrays may be empty unless noted.
4. The stage gap register exists and its `stage` equals the stage number.

| Stage | Artifacts |
|-------|-----------|
| 1 | `requirements_analysis.json`, `quality_attributes.json`, `drivers.json`, `stage1_assumptions_gaps.json` |
| 2 | `pattern_candidates.json`, `pattern_compatibility.json`, `alternatives.json`, `stage2_assumptions_gaps.json` |
| 3 | `alternative_evaluation.json`, `trade_off_analysis.json`, `alternative_selection.json`, `stage3_assumptions_gaps.json` |
| 4 | `adr.md`, `architecture_diagram.mmd`, `stage4_assumptions_gaps.json` |
| package | `output/architecture_decision.json`, `output/adr.md`, `output/architecture_diagram.mmd`, `output/assumptions_and_gaps.json` |

## Stage-specific checks

**Stage 1**
- Every requirement in `00_input/functional_requirements.md` appears in `requirements` (count and IDs match).
- All `source_requirement_ids` resolve. Driver names are unique.
- Boundary (major finding): no pattern, style, tactic, technology, component or alternative is proposed. Stated
  input constraints are allowed. Ambiguities are not "resolved" with invented business rules.

**Stage 2**
- `source_driver_names` / `affected_drivers` / `addressed_drivers` match `drivers.json` names exactly.
- Patterns in compatibility entries and alternatives exist among candidates (or are justified additions).
- Each alternative's `selected_patterns` is not a combination marked `conflicting` without stated conditions.
- At least two alternatives, or a gap entry explaining why only one is supported. Alternatives differ meaningfully.
- Boundary: no evaluation, ranking or selection language ("best", "recommended").

**Stage 3**
- `evaluations` covers every alternative; each covers every requirement ID; statuses use the scale.
- `trade_offs` covers every alternative. No invented numbers presented as measurements.
- `selected_alternative_id` exists; every other alternative is in `rejected_alternatives`.
- The selection is consistent with the evaluation (blocking if the selected alternative has strictly more
  `not_satisfied` requirements than a rejected one without a rationale addressing it).
- `key_limitations` is non-empty if the trade-off analysis lists weaknesses/risks for the selected alternative.

**Stage 4**
- `adr.md` first line starts with `# ADR:`; sections Status, Context, Decision, Rationale, Alternatives Considered,
  Consequences (Positive and Negative), Traceability, Assumptions and Unresolved Gaps are present.
- The Decision names the same alternative as `alternative_selection.json` (blocking if different).
- Traceability cites requirement IDs and driver names that exist. Gap IDs cited exist in the registers.
- `architecture_diagram.mmd` has no code fences, starts with a Mermaid diagram type, `subgraph`/`end` balance,
  components correspond to the selected alternative and do not introduce protocols absent from inputs/alternative.

**Package**
- `architecture_decision.json` validates against `architecture-decision.schema.json`: exactly the four properties,
  `adr_markdown` ≥ 80 chars starting `# ADR:`, `architecture_diagram_mermaid` ≥ 20 chars starting with an allowed
  diagram type, no additional properties.
- `selected_alternative_id` and `selection_rationale` equal the Stage 3 values; `adr_markdown` equals
  `_workspace/artifacts/adr.md`; `architecture_diagram_mermaid` equals the `.mmd` file (compare content; a
  difference is blocking).
- `assumptions_and_gaps.json` contains every entry from the four stage registers.

## Return value

```json
{ "stage": 1, "verdict": "pass|pass_with_findings|fail", "blocking": ["..."],
  "findings": [ { "severity": "blocking|major|minor", "artifact": "drivers.json", "issue": "...", "evidence": "..." } ] }
```

Use `stage: 5` for the package review.
