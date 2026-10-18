# HarnessWeaver Concepts

This document defines the terms used across HarnessWeaver's shared methodology, HarnessSpec, runtime adapters, and case studies. It clarifies the intended boundaries; it does not replace the implementation roadmap or the domain specifications.

## Product and workflow terms

### HarnessWeaver

The project that develops a runtime-neutral contract and tools for designing, validating, evaluating, and improving agent harnesses. Its shared contract is HarnessSpec; its current implementation includes a Python validator and agent skills intended to share harness-design guidance across runtimes.

### Agent harness

A designed workflow that coordinates agent roles, stages, instructions, tools, inputs, outputs, verification, and any human decision points for a task. A harness may be implemented with skills and files, Python orchestration, or another supported runtime.

### Harness design

The process of examining a task, existing project/domain materials, and constraints, then deciding what harness structure and runtime implementation fit. Harness design can reuse supplied artifacts; it does not imply that all domain guidance must be newly authored.

### Harness evolution

The evidence-led process of using observed outcomes and feedback to improve an existing harness while preserving its baseline and provenance. A proposed change may belong to shared methodology, a runtime adapter, domain guidance, or a project-specific harness.

## Contract and implementation terms

### HarnessSpec

A versioned, runtime-neutral description of harness intent and workflow. HarnessSpec records sources, roles, stages, artifact contracts, verification, human gates, and runtime requirements. It describes a harness; it is not itself an executing agent, a runtime configuration, or a domain theory.

### Methodology

Reusable guidance for analyzing a task and designing a harness. It should remain independent of a particular runtime and should not absorb rules that are specific to one domain.

### Domain materials

Knowledge supplied for the task's subject area, such as standards, methods, skills, examples, schemas, or evaluation criteria. A harness-design workflow inspects and reuses applicable materials while recording their source and authority.

### Runtime adapter

The runtime-specific implementation that maps HarnessSpec intent to a particular agent platform or application. An adapter may translate or omit features; it should make unsupported capabilities and meaningful fidelity loss visible.

### Domain application

A software application or reusable workflow that performs work in a specific subject area. It may use one or more harnesses and runtime adapters, while keeping its domain rules distinct from HarnessWeaver's general methodology.

## Evaluation terms

### Case study

A separately maintained project or research artifact used to ground or evaluate HarnessWeaver. A case study provides evidence and examples; its presence in this repository does not transfer its ownership or authorize changes to its source data, ground truth, or history.

### Baseline

The recorded harness version or existing workflow used as a comparison point for an evaluation or evolution. A baseline remains available after revisions so changes can be attributed and compared.

### Run

One execution of a harness under recorded inputs and runtime/model settings. A reproducible run record identifies the spec, harness, inputs, outputs, configuration, checks, and results. Evaluation-only references such as ground truth must remain inaccessible to generation.

### Feedback

An observation from a run or user review that may inform a change. Feedback is evidence to assess, not an automatic instruction to generalize a one-off preference into shared methodology.

## Keep these models distinct

The **HarnessSpec** describes the workflow and contracts of an agent harness. A **software design space** describes the alternative software-design decisions explored by a software-design application. The application may itself use an agent harness, but its design space is a domain model inside that application, not a field or feature of HarnessSpec unless a future contract explicitly defines such a relationship.

Likewise, the software-architecture-agent and architecture-evaluation projects are case studies or domain applications used to examine HarnessWeaver's approach. They are not the HarnessWeaver product itself.

## Source documents

- [Implementation roadmap](docs/harnessweaver-implementation-roadmap.md) — product contract, scope, and implementation sequence.
- [Consolidation plan](docs/consolidation-plan.md) — intended methodology, runtime, and domain boundaries; its repository paths should be kept current as the structure changes.
- [HarnessSpec v0.1 schema](specs/harnessspec/v0.1.schema.json) — machine-readable contract fields.
- [Software design exploration specification](docs/software_design_exploration_agent_harness_spec.md) — domain model and prototype vision for that application.
