# HarnessWeaver Vision and Position

## Purpose

Domain-specific agentic systems are commonly built either as custom applications on agent frameworks or by adapting a general-purpose harness. Both approaches can work well. They also require developers to make consequential choices about methodology, harness structure, agent architecture, and runtime while domain knowledge is still being translated into an executable system.

HarnessWeaver explores a prototyping layer for this work. It makes the domain and its methodology explicit, uses them to generate an evolvable harness, and supports revising that harness before committing to a specific agent architecture or runtime. Its aim is to make domain-specific harnesses quicker to instantiate and change, not to automatically discover an optimal design.

## Vision

HarnessWeaver supports rapid prototyping and evolution of domain-specific agent harnesses. It helps translate domain knowledge and methodology progressively into an executable agentic system while delaying commitment to a particular architecture or runtime.

The resulting harness is a working prototype. A team can evaluate it, change it, and continue evolving it. When the design is sufficiently understood, the team can retain it as a harness or use it as a basis for a more specific implementation, such as a custom agentic application or a specialization of an existing harness.

## The construction problem

Building a domain-specific agentic system involves more than selecting a model and adding domain documents. A team must decide what work the system should perform, how domain methods guide that work, what state should be tracked, which tools and agents are needed, and how the system will run. In an application-first approach, many of these decisions become embedded in framework code. In a harness-specialization approach, they are made within the structure and extension points of an existing harness.

These are useful strategies, but either can make early decisions expensive to revisit. HarnessWeaver treats the harness as something that can be instantiated and evolved during prototyping, before the team commits to a particular realization.

## Three construction strategies

### 1. Custom agentic application

The team starts with a domain problem and its expertise, then builds an application using an agent framework such as LangChain or LangGraph. Workflows, agents, retrieval, tools, state, and other behavior are implemented directly in the application.

This approach gives the team broad control over the system. Domain knowledge and methodology can be encoded in prompts, data sources, tool implementations, schemas, and application logic. The resulting system may be tailored closely to its task. The tradeoff is that the system's design is expressed in implementation choices, so changing the methodology or architecture may require coordinated code changes.

### 2. Manual specialization of an existing harness

The team starts with a general-purpose harness and adapts it to a domain using instructions, skills, tools, resources, subagents, or orchestration. The result inherits the base harness's runtime and conventions.

This can be an efficient path when the existing harness fits the work and its extension points support the needed behavior. Domain-specific instantiation and orchestration still require design work, much of which is performed manually. The resulting flexibility depends on the base harness's modularity and constraints.

### 3. HarnessWeaver

HarnessWeaver starts from task intent, domain knowledge, and an explicit methodology. The methodology includes activities, readiness, artifacts, validation, completion, and semantic state: what meaningful progress has been made, what evidence supports it, and what remains unresolved. HarnessWeaver uses these inputs to generate an inspectable Harness IR and a harness that can be evaluated and revised. Methodology state remains separate from agent working state and runtime bookkeeping, so the agent arrangement can change without redefining domain progress.

The intended benefit is a more direct path from domain method to an executable, changeable harness. The prototype can later be retained or refined into a custom application or a specialization of an existing harness. HarnessWeaver does not currently claim to search all possible harnesses, rank them, or guarantee an optimal result.

## Position relative to existing strategies

| Dimension | Custom agentic application | Harness specialization | `revfactory/harness` (`harness-rev`) | HarnessWeaver |
|---|---|---|---|---|
| Starting point | Domain problem and expertise; implement an application on an agent framework | Existing general-purpose harness | Existing harness repository and its conventions | Domain problem, domain knowledge, and explicit methodology |
| Methodology | Encoded across prompts, workflows, tools, and application logic | Translated manually into instructions, skills, tools, and orchestration | Expressed within the selected harness's configuration, instructions, skills, and workflows | Made explicit as an input to harness generation and revision |
| Harness design | Designed and implemented by the application team | Designed manually around the base harness | Shaped by the selected repository and its extension points | Generated as an editable prototype and revised as understanding develops |
| Agent architecture | Chosen and implemented directly | Largely inherited from the base harness, with possible extensions | Largely shaped by the chosen harness and its supported patterns | Deferred during prototyping; selected or refined for a later realization |
| Runtime and framework | Selected directly | Inherited from the base harness | Inherited from the harness being adapted | Can be committed to after prototyping, subject to available realization paths |
| Evaluation | Application-specific tests, task metrics, and human review | Evaluation in the base harness, supplemented as needed | Evaluation supported or added within the repository workflow | Prototype evaluation informs revisions; it does not establish automatic optimality |
| Evolution | May involve coordinated changes to code, data, prompts, and architecture | Manual changes within the base harness's extension points | Follows the selected harness's conventions and constraints | Intended to support rapid modification of domain knowledge, methodology, and harness structure |
| Portability and reuse | Components can be reused, while the application may remain bespoke | Skills and tools may transfer where compatible | Reuse depends on compatibility with the underlying harness | Components may be reusable where a target realization supports them; portability is not guaranteed |
| Architectural commitment | Usually made during application design and implementation | Commitment to the base harness is made at the outset | Commitment to the selected harness and its extension model is made at the outset | Delayed while the prototype evolves |
| Development speed | Variable; depends on task scope, experience, and framework fit | Can be quick when the base harness fits and extensions are straightforward | Can be quick for changes that fit existing conventions; setup and constraints matter | Aims to reduce the effort of prototyping and revising; comparative speed depends on context |
| Flexibility to adapt to change | Broad control, though changes may require coordinated implementation work | Depends on modularity and base-harness constraints | Depends on repository structure and coupling to the chosen harness | Designed to support changes before choosing a specific realization; does not guarantee lower cost for every change |
| Primary goal | Deliver a domain-specific agentic application | Make a general-purpose harness useful for a domain | Adapt and evolve a particular harness for project use | Rapidly prototype and evolve domain-specific harnesses before committing to a concrete system |

The `harness-rev` column is a high-level characterization of adapting a particular harness repository. Its exact capabilities depend on the repository version and project configuration; it should not be read as a claim about undocumented features.

## What HarnessWeaver contributes

HarnessWeaver's position is a combination of two familiar activities: application engineering and harness specialization. Its contribution is to make task intent, domain knowledge, methodology, and semantic state explicit inputs to a generated, evolvable harness, so a team can work through a domain-specific system in a prototype before settling on a concrete implementation path. A saved HarnessSpec is appropriate when it enables reuse, validation, or controlled evolution; a simple one-off can start from a compact brief.

This places HarnessWeaver at the boundary between domain analysis and implementation. It does not remove the need for engineering judgment. Developers still decide whether the generated structure is suitable, how to evaluate it, and what should be retained or rebuilt in a target system.

## Development speed and adaptability

The expected advantage is most plausible during early prototyping and repeated changes to domain methodology. When domain knowledge or process assumptions change, making those inputs explicit may make it easier to revise the harness than to locate and coordinate changes spread across an application or constrained by a base harness.

This is a design rationale, not an empirical performance result. Actual development speed and change effort depend on the task, the quality of the domain representation, the generated harness, developer experience, and the available runtime or target harness. Comparative studies should measure time to a useful prototype, effort to accommodate representative changes, and the quality of resulting systems.

## Scope and claims

HarnessWeaver is positioned as a way to generate and evolve domain-specific harnesses efficiently before committing to a specific agentic system. The current position is deliberately narrower than general design-space exploration.

The approach does not claim that HarnessWeaver:

- automatically discovers the best harness or agent architecture;
- removes the need for domain experts or engineering judgment;
- guarantees portability across runtimes and harnesses;
- is faster or more flexible for every task or team; or
- replaces custom application development or manual harness specialization.

Instead, it offers an intermediate prototyping strategy. Its value should be demonstrated through concrete examples showing how explicit domain methodology is translated into a working harness and how that harness can be revised as requirements or understanding change.

## Evaluation questions

The position can be examined with practical questions:

1. How quickly can a team produce a useful domain-specific harness prototype from explicit domain and methodology inputs?
2. How much effort is required to revise the prototype after a meaningful change in domain knowledge or process?
3. Which parts of the generated harness can be retained in a custom application or existing harness?
4. What quality, reliability, or maintainability tradeoffs appear compared with direct application development and manual harness specialization?

These questions distinguish a practical prototyping contribution from a claim that one construction strategy is universally superior.

The current implementation direction and paper-by-paper evidence boundaries are summarized in the [implementation roadmap](harnessweaver-implementation-roadmap.md) and [research foundations](research-foundations.md).
