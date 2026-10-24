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

A versioned, runtime-neutral artifact for describing harness intent and workflow. It can record sources, roles, stages, artifact contracts, verification, human gates, and runtime requirements, and may be extended to represent domain knowledge and methodology state. A saved HarnessSpec is useful when reuse, validation, or evolution justifies it; simple one-offs may use a compact brief. HarnessSpec is not itself an executing agent, a runtime configuration, or a domain theory.

### Methodology

The domain-specific process for doing the work: activities, techniques, dependencies or readiness, artifacts, validation, semantic state, and completion conditions. Agents enact the methodology and maintain its state. Methodology is distinct from the arrangement of agents and runtime execution details.

### Intent

The task goal, success criteria, constraints, and human decision requirements that determine what a harness should accomplish. Intent may be recorded in HarnessSpec or supplied in a compact brief for a one-off.

### Domain knowledge

Concepts, terminology, evidence, standards, and other knowledge about the task's subject area. Domain knowledge is distinct from the methodology used to perform work in that area.

### Methodology state

The semantic progress of work through a methodology, including completed or partial activities, supporting evidence, gaps, confidence, and unresolved questions. It is shared across agents and distinct from agent working state (such as role-specific notes) and runtime state (such as messages, tool calls, and checkpoints).

### Harness IR

An inspectable intermediate representation connecting intent, domain knowledge, and methodology to an agent-harness realization. In this repository it is the HarnessSpec plus its `design-notes.md`. The generation skills produce it, materialize targets from it, and revise it. It does not imply search over candidate harnesses or optimization for a best design.

### Domain materials

Knowledge supplied for the task's subject area, such as standards, methods, skills, examples, schemas, or evaluation criteria. A harness-design workflow inspects and reuses applicable materials while recording their source and authority.

### Authored sources

What the architect provides for a pilot, under `pilots/<pilot>/sources/`: `intent.yaml`, `methodology.yaml`, and `domain/` (sources index, portable skills, output contracts, references). Authored sources contain no runtime constructs and no case data. They may also be drafted by harvesting an existing application, then reviewed.

### Generation skills

The two skills a coding agent uses to produce and revise harnesses: `harness` (intake, design, target selection, materialization) and `evolve` (feedback-driven revision). They live in `src/harnessweaver/skills/` and ask the user through question gates G0–G6, whose answers are recorded in `design-notes.md` and can be replayed from `harness-answers.yaml`.

### Target

A runtime form the `harness` skill can materialize: currently a **Claude Code project** or a **DeepAgents stage pipeline**. Each target has a reference under `references/targets/` that defines its mapping. The target is chosen at gate G4, never in the authored sources.

### Runtime adapter

The runtime-specific part that realizes HarnessSpec intent on a particular platform. Here it has two pieces. The **target reference** (mapping rules the generation skill applies) produces data files. The **host** executes those files: the Claude Code CLI, the HarnessWeaver DeepAgents stage host, or an existing application such as SARA's pipeline. An adapter may translate or omit features; it makes unsupported capabilities and meaningful fidelity loss visible in the materialization report.

### Materialization report

The fidelity record each target writes (`materialization-report.md`): every spec stage, role, artifact, verification, human gate and the semantic state, each marked mapped, approximated or unsupported, plus decisions, manual setup and what was not verified.

### Reference realization

A hand-written runtime realization kept for comparison with generated ones, such as `pilots/atam/claude-plugin/` and the multi-profile ATAM DeepAgents runner. It is not on the generated path.

### Domain application

A software application or reusable workflow that performs work in a specific subject area. It may use one or more harnesses and runtime adapters, while keeping its domain rules distinct from HarnessWeaver's general methodology.

## Evaluation terms

### Case study

A separately maintained project or research artifact used to ground or evaluate HarnessWeaver. A case study provides evidence and examples; its presence in this repository does not transfer its ownership or authorize changes to its source data, ground truth, or history.

### Baseline

The recorded harness version or existing workflow used as a comparison point for an evaluation or evolution. A baseline remains available after revisions so changes can be attributed and compared. The **generation baseline** is the upstream revfactory/harness v2.1.0 skill set (`baselines/`), run in its English translation under the same inputs as the HarnessWeaver skills, for Claude-runtime comparisons.

### Sandbox

An isolated directory in which one step runs and is recorded. A **generation sandbox** gives a coding agent read-only sources, a pinned skill set and one writable `generated/` area. An **execution sandbox** gives a generated bundle only a case's generation inputs, one writable workspace and an output area. Evaluator-only data never enters a sandbox; checks run from outside it.

### Case binding

The file (`pilots/<pilot>/cases/<case>.yaml`) that names which parts of a case are generation inputs (copied into an execution sandbox) and which are evaluator-only (read only by checks).

### Run

One execution of a harness under recorded inputs and runtime/model settings. A reproducible run record identifies the spec, harness, inputs, outputs, configuration, checks, and results. Evaluation-only references such as ground truth must remain inaccessible to generation.

### Feedback

An observation from a run or user review that may inform a change. Feedback is evidence to assess, not an automatic instruction to generalize a one-off preference into shared methodology.

## Keep these models distinct

The **HarnessSpec** describes the task intent and contracts for an agent harness. A **software design space** describes the alternative software-design decisions explored by a software-design application. The application may itself use an agent harness, but its design space is a domain model inside that application, not a field or feature of HarnessSpec unless a future contract explicitly defines such a relationship.

Likewise, the software-architecture-agent and architecture-evaluation projects are case studies or domain applications used to examine HarnessWeaver's approach. They are not the HarnessWeaver product itself.

## Source documents

- [Implementation roadmap](docs/harnessweaver-implementation-roadmap.md) — product contract, scope, and implementation sequence.
- [Research foundations](docs/research-foundations.md) — evidence and limitations from the papers used to ground the current direction.
- [Consolidation plan](docs/consolidation-plan.md) — intended methodology, runtime, and domain boundaries; its repository paths should be kept current as the structure changes.
- [CAIN 2027 approach](docs/cain-2027/APPROACH.md) and [status](docs/cain-2027/STATUS.md) — the current generation approach, pilots and remaining work.
- [Generation skills](src/harnessweaver/skills/README.md) — `harness` and `evolve`.
- [HarnessSpec v0.1](specs/harnessspec/v0.1.schema.json) and [v0.2](specs/harnessspec/v0.2.schema.json) schemas — machine-readable contract fields.
- [Software design exploration specification](docs/software_design_exploration_agent_harness_spec.md) — domain model and prototype vision for that application.
