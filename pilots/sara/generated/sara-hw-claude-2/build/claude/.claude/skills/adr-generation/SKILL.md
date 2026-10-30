---
name: adr-generation
description: "Generate an Architecture Decision Record documenting the selected architectural decision and its rationale. SARA Stage 4, task 1; executed only by the decision-recorder agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/adr-generation/SKILL.md (SARA @528ae7ce, sha256 6a9c1e45a78b9585f659cd7bd774b98ac198f2e9f9d0f2ff309b0b765468d47a). Adapted for the Claude Code bundle; see materialization-report.md. -->

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

- _workspace/artifacts/alternative_evaluation.json
- _workspace/artifacts/trade_off_analysis.json
- _workspace/artifacts/alternative_selection.json

Also read, read-only (adaptation A6), because the procedure below needs them for
context, alternative names and traceability:

- _workspace/artifacts/requirements_analysis.json
- _workspace/artifacts/quality_attributes.json
- _workspace/artifacts/drivers.json
- _workspace/artifacts/alternatives.json

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

_workspace/artifacts/adr.json

as a JSON object with exactly two keys (adaptations A2, A3):

- `selected_alternative_id`: copied exactly from alternative_selection.json
- `adr_markdown`: the complete ADR Markdown as one string, starting with `# ADR:`

Use the following structure for `adr_markdown`:

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

After writing the file, check that `adr_markdown` starts with `# ADR:` (adaptation A5),
then read it back and verify that it is valid JSON.
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact adr`

The contract is `references/adr.schema.json`.