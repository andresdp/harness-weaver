---
name: adr-generation
description: Generate an Architecture Decision Record documenting the selected architectural decision and its rationale.
---

# SKILL: ADR Generation

## Objective

Generate a complete and self-contained Architectural Decision Record (ADR)
for the architectural alternative selected in Stage 3.

The ADR is a final architectural artifact.

It must document the architectural decision clearly enough that a software
architect can understand:

- why the decision was necessary
- what was decided
- why the selected alternative was preferred
- which important alternatives were considered
- what consequences result from the decision

## Input Artifacts

Read:

- /alternative_evaluation.json
- /trade_off_analysis.json
- /alternative_selection.json

## Procedure

1. Identify the selected alternative from alternative_selection.json.

2. Use the requirements, drivers, evaluations, and trade-offs to reconstruct
   the context necessary to understand the decision.

3. Describe the architectural decision precisely.

4. Explain the main reasons supporting the decision.

5. Describe the important positive and negative consequences.

6. Identify the relevant alternatives considered and explain why they were
   not selected.

7. Preserve traceability to the most important requirements and architectural
   drivers.

The ADR must synthesize the previous artifacts rather than simply copying
their content.

## Rules

- The ADR must document the decision already made.
- Do not introduce a new alternative.
- Do not change the selected alternative.
- Clearly distinguish positive and negative consequences.
- Include relevant rejected alternatives and why they were not selected.
- Preserve traceability to requirements and drivers.
- Do not generate implementation details unless they are part of the selected
  architectural alternative.

## Expected Output

Write:

/adr.md

Use the following structure:

```
# ADR: <Decision Title>

## Status

Accepted

## Context

Describe the architectural problem or situation that required a decision.

Include only the context necessary to understand the decision.

The context should be grounded in the requirements and architectural drivers.

## Decision

State clearly and unambiguously what architecture or architectural solution
was selected.

Identify the main architectural patterns or design choices that constitute
the selected alternative.

## Rationale

Explain why this alternative was selected.

Focus on the most important architectural reasons.

The rationale MUST be based on:

- requirement satisfaction (alternative_evaluation.json)
- architectural driver satisfaction (alternative_evaluation.json)
- quality attribute considerations (alternative_evaluation.json)
- relevant trade-offs (trade_off_analysis.json)

Do not reproduce the complete Stage 3 evaluation.

## Alternatives Considered

For each important rejected alternative:

### <Alternative Name>

Explain briefly:

- what the alternative proposed
- why it was not selected
- which requirement, driver, quality attribute, or trade-off influenced
  the rejection

Only include alternatives that were meaningfully considered.

## Consequences

### Positive Consequences

List the important benefits resulting from the decision.

### Negative Consequences

List the important costs, limitations, risks, or compromises resulting from
the decision.

Do not hide significant disadvantages of the selected architecture.

## Traceability

List only the most relevant links between the decision and:

- requirements
- quality attributes
- architectural drivers
```

After writing the file, read it back and verify that it is valid Markdown.