---
name: HarnessWeaver
last_updated: 2026-10-18
---

# HarnessWeaver Strategy

## Purpose

Software architects currently assemble agent workflows ad hoc. Custom agents and workflows take time to build and are hard to adapt or use, while isolated skills require manual orchestration. This makes it difficult to learn what works for architecture evaluation and design exploration before investing in a complex architecture agent.

## Positioning

HarnessWeaver uses a shared, runtime-neutral description to generate a task-specific harness that can be tried as skills or as a DeepAgents backend, with the architect choosing the form. Keep the spec light enough for quick experiments; a simple one-off may be tried without a saved HarnessSpec when the contract adds more overhead than value. Earlier meta-harness work has been tried in other domains, but the software architecture focus remains to be validated.

## Users

**Primary:** Software architects — they hire HarnessWeaver to quickly generate task-specific harnesses for software architecture evaluation and design exploration, then try those ideas before committing to a complex architecture agent.

## Boundaries

- Keep the first proof focused on software architecture evaluation and design exploration.

_Resist a change when:_ it broadens the first proof to non-architecture domains before those architecture workflows have been evaluated.

## Key metrics

- **Speed to generate** — time to produce a usable harness; definition and measurement location to be defined.
- **Functional completeness** — whether generated agents, skills, or backend code provide the functions needed for the task; definition and measurement location to be defined.
- **Result accuracy** — accuracy of the harness outputs for the architecture task; definition and measurement location to be defined.

## Tracks

Investment tracks are not set yet. Worth revisiting when near-term priorities are clearer.
