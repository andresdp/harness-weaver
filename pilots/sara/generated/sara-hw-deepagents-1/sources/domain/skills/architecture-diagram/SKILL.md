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

- /alternative_evaluation.json
- /trade_off_analysis.json
- /alternative_selection.json
- /adr.json

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

Write the Mermaid source directly to:

/architecture_diagram.mmd

The file must contain valid Mermaid syntax.

Prefer: flowchart LR

for component-level architecture diagrams.

Do not wrap the Mermaid source in Markdown code fences inside the .mmd file.