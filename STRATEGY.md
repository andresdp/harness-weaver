---
name: HarnessWeaver
last_updated: 2026-10-18
---

# HarnessWeaver Strategy

## Purpose

Software architects currently build domain-specific agent systems ad hoc: custom applications encode methodology across code and orchestration, while harness-based skills still require manual instantiation and coordination. Both make it costly to learn from a working prototype and revise it as domain understanding changes.

## Positioning

HarnessWeaver makes task intent, domain knowledge, and methodology explicit, including the semantic state that describes meaningful progress through the methodology. It uses these assets to create an inspectable Harness IR and a working, editable prototype, which can be evaluated and evolved before the architect commits to a concrete agent architecture or runtime. The same design may be materialized as a skills-based harness or a Python/DeepAgents application where supported. Keep the representation proportionate: a simple one-off may be tried without a saved HarnessSpec when the formal artifact costs more than it helps. Methodology and its state remain distinct from agent-specific and runtime execution state. The software-architecture use cases remain to be validated.

## Users

**Primary:** Software architects — they hire HarnessWeaver to quickly generate task-specific harnesses for software architecture evaluation and design exploration, then try those ideas before committing to a complex architecture agent.

## Boundaries

- Keep the first proof focused on software architecture evaluation and design exploration.
- Treat generation and feedback-driven evolution of a viable prototype as the current contribution. Do not claim autonomous search, ranking, or discovery of an optimal harness.
- Treat portability as a design aim whose fidelity must be demonstrated for each runtime; runtime-neutral representation does not prove interchangeable implementations.

_Resist a change when:_ it broadens the first proof to non-architecture domains before those architecture workflows have been evaluated.

## Key metrics

- **Time to a useful prototype** — time and effort to generate a harness that an architect can inspect and try.
- **Change effort** — effort to accommodate representative changes to domain knowledge or methodology.
- **Work quality** — methodology coverage, evidence-grounded outputs, and usefulness as judged against case-specific criteria.
- **Retention and transition** — which prototype artifacts are retained as a harness or carried into a dedicated implementation.

Definitions, baselines, and measurement locations remain to be established in the case studies.

## Tracks

Investment tracks are not set yet. Worth revisiting when near-term priorities are clearer.
