---
name: adr-generation
description: SARA Stage 4, task 1. Writes a complete, self-contained Architecture Decision Record (Markdown, starting "# ADR:") for the alternative selected in Stage 3 — context, decision, rationale, alternatives considered, consequences, traceability, and assumptions/unresolved gaps — to adr.md. Used by the sara-decision-documenter agent inside the sara-orchestrator run; not for making or changing the decision.
---

# ADR Generation

Source: SARA `stage4-architecture_decision/skills/adr-generation` (adapted paths; one appended section, below).

## Objective

Produce a self-contained ADR so a software architect understands why the decision was necessary, what was decided,
why the selected alternative was preferred, which alternatives were considered, and what consequences follow.

## Inputs

- Primary: `_workspace/artifacts/alternative_evaluation.json`, `trade_off_analysis.json`, `alternative_selection.json`
- Traceability context: `requirements_analysis.json`, `quality_attributes.json`, `drivers.json`, `alternatives.json`
- Gap registers: `stage1_assumptions_gaps.json`, `stage2_assumptions_gaps.json`, `stage3_assumptions_gaps.json`

## Procedure

1. Identify the selected alternative from `alternative_selection.json` and its definition in `alternatives.json`.
2. Use the requirements, drivers, evaluations and trade-offs to reconstruct the context needed to understand the decision.
3. Describe the decision precisely. 4. Explain the main reasons. 5. Describe positive and negative consequences.
6. Identify the relevant alternatives considered and why they were not selected.
7. Preserve traceability to the most important requirements and drivers.
8. Summarize the open assumptions and unresolved gaps from the stage registers (harness addition).

Synthesize the previous artifacts rather than copying them.

## Rules

- Document the decision already made; do not introduce or change an alternative.
- Clearly separate positive and negative consequences; do not hide significant disadvantages.
- Include meaningfully considered rejected alternatives and why they were not selected.
- Refer to requirements by ID and drivers by exact name so links can be checked.
- No implementation details unless they are part of the selected alternative.
- The first line must be exactly `# ADR: <Decision Title>` with no preceding blank line — the output contract
  requires the `adr_markdown` field to start with `# ADR:`.

## Output

Write `_workspace/artifacts/adr.md` with this structure:

```markdown
# ADR: <Decision Title>

## Status

Accepted

## Context

The architectural problem that required a decision, grounded in requirements and drivers. Only necessary context.

## Decision

What architecture was selected (state the alternative ID and name), and its main patterns / design choices.

## Rationale

Why it was selected, based on requirement satisfaction, driver satisfaction and quality-attribute considerations
(alternative_evaluation.json) and relevant trade-offs (trade_off_analysis.json). Do not reproduce the full evaluation.

## Alternatives Considered

### <Alternative Name>

What it proposed; why it was not selected; which requirement, driver, quality attribute or trade-off drove the rejection.

## Consequences

### Positive Consequences

### Negative Consequences

## Traceability

The most relevant links between the decision and requirements, quality attributes and drivers
(a compact table is fine: Decision element | Requirement IDs | Quality attributes | Drivers).

## Assumptions and Unresolved Gaps

Open ambiguities, assumptions the selected alternative relies on, `unclear` evaluations and process gaps, each
with its register ID (for example `S1-G2`). Write "None recorded" only if every register is empty.
```

The last section is a harness addition (not in the SARA template) so that assumptions and gaps travel with the ADR
inside the final package. After writing, read the file back and verify it is well-formed Markdown.
