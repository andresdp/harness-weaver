---
name: architecture-diagram
description: "Generate a high-level architecture diagram representing the selected architectural decision. SARA Stage 4, task 2; executed only by the decision-recorder agent inside the sara-architecture-orchestrator workflow. Do not use for general architecture questions outside that workflow."
---
<!-- Copied from sources/domain/skills/architecture-diagram/SKILL.md (SARA @528ae7ce, sha256 1d967396a7efe4176fb5ffd0e5f5bddac2e00fb64affff3453f014d840476df5). Adapted for the Claude Code bundle; see materialization-report.md. -->

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

- _workspace/artifacts/alternative_evaluation.json
- _workspace/artifacts/trade_off_analysis.json
- _workspace/artifacts/alternative_selection.json
- _workspace/artifacts/adr.json

Also read, read-only (adaptation A6):

- _workspace/artifacts/requirements_analysis.json
- _workspace/artifacts/alternatives.json

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

Write the final decision package (adaptations A2, A7) as JSON to:

_workspace/artifacts/architecture_decision.json

It is a JSON object with exactly these four keys:

- `architecture_diagram_mermaid`: the Mermaid source as one string. It must contain valid Mermaid
  syntax and start with the diagram keyword. Prefer: flowchart LR for component-level architecture
  diagrams. Do not wrap the Mermaid source in Markdown code fences.
- `selected_alternative_id`: copied unchanged from alternative_selection.json.
- `selection_rationale`: copied unchanged from alternative_selection.json.
- `adr_markdown`: copied unchanged from adr.json.

Copy the last three values character for character; do not summarize, correct or re-evaluate them.

After writing the file, read it back and verify that it is valid JSON.
Then run the schema check and fix the artifact until it passes:

`python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --artifact architecture_decision`

The contract is `references/architecture-decision.schema.json`.
