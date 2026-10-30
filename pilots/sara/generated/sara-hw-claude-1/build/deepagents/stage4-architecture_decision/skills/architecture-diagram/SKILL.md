---
name: architecture-diagram
description: Generate a high-level architecture diagram representing the selected architectural decision.
---

# SKILL: Architecture Diagram

## Objective

Generate a high-level component architecture diagram that concretely
represents the architectural alternative selected in Stage 3.

The diagram is a final architecture artifact.

It must provide enough detail for a software architect to understand:

- the main architectural components
- the responsibility of each component
- the main interactions between components
- relevant external actors or systems
- important data or communication boundaries

## Input Artifacts

Read:

- /artifacts/alternative_evaluation.json
- /artifacts/trade_off_analysis.json
- /artifacts/alternative_selection.json
- /artifacts/adr.json (the ADR is the `adr_markdown` field)

Also read, for the selected alternative's patterns and the project
requirements (read-only):

- /artifacts/alternatives.json
- /artifacts/requirements_analysis.json

## Procedure

1. Read the selected alternative.

2. Read the ADR to understand the architecture that must be represented.

3. Identify the major architectural components required by the selected
   solution.

4. Assign a concise architectural responsibility to each component.

5. Identify the main relationships between components.

6. Include relevant external actors, systems, or existing resources when
   necessary to understand the architecture.

7. Represent the architecture using Mermaid.

The diagram must describe the selected architecture rather than proposing a
new one.

## Component Modeling Rules

Components should represent meaningful architectural responsibilities.

Examples include:

- API Gateway
- business services
- domain services
- repositories
- databases
- external systems
- client applications

Do not include:

- classes
- methods
- individual functions
- low-level implementation details
- framework-specific objects
- unnecessary infrastructure details

unless they are explicitly relevant to the selected architecture.

## Relationships

Every relationship should communicate a meaningful architectural interaction.

Where useful, annotate relationships with the communication mechanism, such
as:

- HTTP/REST
- synchronous request
- asynchronous event
- message
- data access

Do not invent protocols or communication mechanisms that are not supported by
the selected alternative or requirements.

## Diagram Detail

The diagram should be detailed enough to represent the selected architecture
but should remain understandable at a glance.

Use Mermaid subgraphs when they improve architectural clarity.

The actual diagram must be derived from the selected alternative and project
requirements.

## Expected Output

Write the final architecture decision package to:

/artifacts/architecture_decision.json

The file is a JSON object with exactly these four keys:

```
{
  "selected_alternative_id": "A1",
  "selection_rationale": "...",
  "adr_markdown": "# ADR: ...",
  "architecture_diagram_mermaid": "flowchart LR\n    ..."
}
```

- `architecture_diagram_mermaid` is the diagram produced by this task. It
  MUST contain valid Mermaid syntax and start with the diagram keyword.
  Prefer: flowchart LR for component-level architecture diagrams.
  Do not wrap the Mermaid source in Markdown code fences inside the string.
  Encode line breaks as `\n` inside the JSON string.
- `selected_alternative_id` and `selection_rationale` are copied exactly from
  /artifacts/alternative_selection.json.
- `adr_markdown` is copied exactly from /artifacts/adr.json.

Copy these three values character for character. Do not summarize, rewrite,
reformat or extend them, and do not add other keys.

Correct:
`"selection_rationale"` is the exact string from alternative_selection.json.

Incorrect:
`"selection_rationale"` is a shorter paraphrase written for the package.

After writing the file, read it back and verify that it is valid JSON, that it
has exactly these four keys, that `architecture_diagram_mermaid` starts with a
Mermaid diagram keyword, and that the three copied values equal their sources.

This is the final task of Stage 4.

<!-- HarnessWeaver: adapted from SARA backend/app/agents/stage4-architecture_decision/skills/architecture-diagram/SKILL.md @528ae7ce.
Changed: (A3, harvest defect D2) the ADR input is /artifacts/adr.json written by ADR Generation;
(A2/A7) instead of /architecture_diagram.mmd, this task writes the final package /artifacts/architecture_decision.json
(contracts/architecture-decision.schema.json, a pilot contract), holding its Mermaid source plus three values copied unchanged,
because the host has no deterministic assembly step; (A6) alternatives and requirements declared as read-only inputs;
(A5) read-back sentence added (the source had none). Objective, procedure, component modeling rules, relationships and diagram detail are unchanged. -->
