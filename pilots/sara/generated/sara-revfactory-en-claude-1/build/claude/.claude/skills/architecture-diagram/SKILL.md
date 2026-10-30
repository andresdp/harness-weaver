---
name: architecture-diagram
description: SARA Stage 4, task 2. Draws a high-level Mermaid component diagram (prefer "flowchart LR", raw source without code fences) of the architecture selected in Stage 3 and documented in the ADR, and writes architecture_diagram.mmd. Used by the sara-decision-documenter agent inside the sara-orchestrator run; not for proposing a new architecture or for general diagramming requests.
---

# Architecture Diagram

Source: SARA `stage4-architecture_decision/skills/architecture-diagram`. Adaptation: the source lists `/adr.json` as
an input while the ADR skill writes `/adr.md`; this harness reads `_workspace/artifacts/adr.md`.

## Objective

A high-level component diagram that concretely represents the selected alternative, enough for an architect to see
the main components and their responsibilities, the main interactions, relevant external actors or systems, and
important data or communication boundaries.

## Inputs

- `_workspace/artifacts/alternative_evaluation.json`
- `_workspace/artifacts/trade_off_analysis.json`
- `_workspace/artifacts/alternative_selection.json`
- `_workspace/artifacts/adr.md`
- `_workspace/artifacts/alternatives.json`, `requirements_analysis.json` (to stay faithful to the selected alternative)

## Procedure

1. Read the selected alternative. 2. Read the ADR to understand the architecture to represent.
3. Identify the major components the selected solution requires. 4. Give each a concise responsibility.
5. Identify the main relationships. 6. Include external actors, systems or existing resources when needed.
7. Represent it in Mermaid. The diagram describes the selected architecture; it does not propose a new one.

## Component modeling rules

Components represent meaningful architectural responsibilities (for example API gateway, business or domain
services, repositories, databases, external systems, client applications). Do not include classes, methods,
functions, low-level or framework-specific objects, or unnecessary infrastructure unless explicitly relevant.

## Relationships

Every edge communicates a meaningful interaction. Annotate with the mechanism where useful (HTTP/REST, synchronous
request, asynchronous event, message, data access). Do not invent protocols that the selected alternative or the
requirements do not support.

## Detail and syntax

- Detailed enough to represent the architecture, understandable at a glance. Use subgraphs when they add clarity.
- Prefer `flowchart LR`. The very first line must be the diagram type (contract pattern
  `^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|C4Context|C4Container|C4Component|C4Dynamic)`).
- Keep the syntax conservative so it renders: alphanumeric node IDs, labels in double quotes
  (`api["Booking Service<br/>handles reservations"]`), edge labels as `-->|"HTTP/REST"|`, no parentheses or
  brackets unquoted inside labels, every `subgraph` closed with `end`.
- Optionally reference the ADR's component names exactly so the reviewer can match them.

## Output

Write the raw Mermaid source to `_workspace/artifacts/architecture_diagram.mmd`. Do not wrap it in Markdown code
fences. Read the file back and check the first line, balanced `subgraph`/`end`, and that every edge endpoint is a
declared node.
