# HarnessWeaver: Conversation Context and Working Position

> **Provenance.** This file reconstructs the HarnessWeaver discussion from the retained conversation data for **“Brainstorming Python Harness Options”** and the topic summary supplied with the request. The thread reader returned only a bounded set of turns and excerpts; it did not expose a complete verbatim transcript. Text under **Verbatim retained prompts** is quoted from messages visible in that retained data. The remaining narrative is a chronological synthesis, not a claim of exact wording. Where a topic is present only in the supplied summary, it is marked **[Reconstructed from retained summary]**.

## Purpose

This document preserves the project framing, conceptual distinctions, and figure/table requirements discussed for HarnessWeaver. Treat it as project context and a working specification, not as a finalized research claim or a complete transcript.

## 1. Starting point: two ad-hoc construction strategies

**Verbatim retained user prompt:**

> “In my view, most (domain-specific) agentic systems today are created in 2 ad-hoc manners:
>
> 1. Leverage your domain knowledge and create an agentic system (workflow, multi-agents, RAG, etc) on top of an existing library (e.g., Langchain, Langgraph, etc.). This is one-of-a-kind system
> 2. Depart from a harness, like a coding agent, and leverage your domain knowledge to create a set of skills (and eventually sub-agents) with some orchestration, which can be plugged in and used. This is a bit closer to HarnessWeaver, but doing all the instantiation of the agentic system manually”

The two routes were characterized as follows:

1. **Application-first engineering.** Domain expertise is encoded directly in a custom application built on an agent framework: workflows, agents, retrieval, tools, state, and orchestration. It can be a strong solution, but the design is often specific to that application and its framework.
2. **Harness specialization.** Start with a general-purpose harness and manually add domain instructions, skills, tools, subagents, and orchestration. This encourages reuse of an existing harness, but developers still make most instantiation and design decisions themselves.

The initial HarnessWeaver idea was to bridge the two: create a domain-specific harness efficiently, allow it to take forms realizable through either route, and use the prototype to inform later refinement or implementation through conventional engineering.

## 2. Initial HarnessWeaver framing, then a deliberate narrowing

The first assistant response framed HarnessWeaver as an explicit, iterative harness-construction process, with domain knowledge, methodology, intent, evaluation, and multiple realizations made visible. It raised a potentially ambitious “design-space exploration” interpretation: generate substantially different candidate harness architectures and compare them.

The user corrected that scope:

**Verbatim retained user position:**

> “I agree with the general view, but I don´t think the goal of harness weaver is (yet) exploring alternative harnesses -- this is much of a strecht, I´d say humbly that harness weaver is more about being flexible to generate alternative harnesses or evolve an existing ones quickly, before committing to a very specific agentic system for a domain.”

This correction is central. The current, more moderate and demonstrable position is about **rapid prototyping, generation, and evolution**, not autonomous search for an optimum. Alternative realizations may be generated or an existing one evolved as practical development needs arise; claiming a systematic search over a design space would overstate the present system.

The assistant reformulated the core idea around **premature commitment**: domain assumptions tend to become embedded early in framework nodes, agent classes, retrieval pipelines, tool wiring, or harness-specific files. HarnessWeaver inserts an explicit prototyping step before a team commits to a specific architecture or runtime.

### Working positioning statement

> **HarnessWeaver supports rapid prototyping and evolution of domain-specific agent harnesses, allowing domain knowledge and methodology to be progressively translated into executable agentic systems without prematurely committing to a particular agent architecture or runtime.**

The intended promise is to lower the cost of reaching a useful prototype and changing it as domain understanding improves. The objective is not to discover an “optimal harness.”

### Progressive or delayed commitment

The proposed development loop is:

```text
Understand the domain
        ↓
Capture domain knowledge and methodology explicitly
        ↓
Generate a lightweight working harness
        ↓
Use and evaluate it
        ↓
Learn and evolve it
        ↺
        ↓ when sufficiently understood
Commit to a more specific implementation if needed
```

**Progressive commitment** means architectural commitment can increase as understanding of the domain, methodology, and effective agent behavior increases. A successful prototype can remain a lightweight harness or be engineered into a dedicated application.

## 3. Conceptual separation: intent, domain, methodology, harness, runtime

The discussion distinguishes several assets and layers that should not be collapsed into one “agent prompt” or generated codebase.

### IntentSpec

**[Reconstructed from retained summary]** Intent describes the task the system is meant to accomplish, its goals, success criteria, and constraints. Evaluation criteria belong early enough to influence design, rather than being appended only as downstream tests.

Illustrative fields discussed include the goal (for example, evaluate architecture solutions), quality criteria such as evidence-grounded findings and risk/tradeoff coverage, and constraints such as cost or human review.

### DomainSpec

**[Reconstructed from retained summary]** DomainSpec represents domain concepts, knowledge, terminology, and relevant artifacts. In Architecture Evaluation these might include quality attributes, architecture tactics, ADRs, architectural styles and patterns, risks, and architecture views.

Domain knowledge is distinct from knowing **how practitioners carry out a process**. Packaging reference material or skills can provide knowledge, but does not by itself specify a methodology.

### Methodology as a first-class asset

Methodology represents the process of doing domain work: activities, dependencies or readiness, techniques, inputs and outputs, validation, state, and completion conditions. It should be explicit and reusable alongside domain knowledge, skills, and tools.

For example, an Architecture Evaluation methodology might move through understanding context, identifying drivers, assessing architecture evidence, analyzing quality-attribute implications, identifying risks and sensitivities, examining tradeoffs, and synthesizing findings.

**Verbatim retained principle:**

> “Methodology defines the process and its meaningful state; agents enact the methodology and maintain that state.”

An agent is therefore not merely a sequence of prompts. It acts on methodology state, produces evidence or artifacts, and updates that state. The state belongs to the harness/methodology model; agents observe and update it. This lets a single methodology state model persist across different agent arrangements.

### Harness IR

**[Reconstructed from retained summary; details also appear in visible assistant excerpt]** Harness IR is the explicit intermediate representation separating the intent, domain assets, and methodology from their concrete agentic realization. The generator and evolver can manipulate it without scattering domain intent across generated files. It can then be materialized for different runtimes or implementation styles.

Its immediate justification is **separation, inspectability, and portability**, not being a search representation. A simple lifecycle is:

```text
IntentSpec + DomainSpec + Methodology
                    ↓
                 Generator
                    ↓
                 Harness IR
                    ↓
         runtime-specific materialization
                    ↓
             evaluation and evolution
```

### Runtime and evaluation

Runtime is where the harness executes: agents, tools, skills, orchestration, context, memory, and runtime-specific state. A runtime is an implementation target, not the methodology itself.

Evaluation checks whether a harness and its outputs meet the declared goals and criteria. It informs redesign and evolution; it is part of the construction loop, not merely a final QA step.

### Evolution levels

**[Reconstructed from retained summary]** Keep two meanings separate:

- **Harness evolution:** revise one prototype based on its use and evaluation (prompts, skills, workflow, models, tools, or architecture).
- **Generator evolution:** use evidence from many harness experiments to improve future generation. This was discussed as a possible longer-term research direction, not a current core claim.

Likewise, “generation” means producing a working harness; “evolution” means refining it based on experience; “synthesis” can be an umbrella term for translating specifications into a realization. Avoid using “synthesis” in a way that implies autonomous optimal-design search.

## 4. Methodology state and agents

The retained assistant response proposes that a methodology include:

```text
Activities       — what can or should be done
Techniques       — how an analysis is performed
Artifacts        — what is consumed and produced
State            — where the work stands semantically
Readiness        — when an activity can meaningfully run
Validation       — how outputs are assessed
Completion       — when the methodology has achieved its goal
```

For the Architecture Evaluation pilot, state should be domain-semantic, not only execution bookkeeping such as `messages` and `current_step`. Candidate state includes context, architectural drivers, architecture description, quality attributes, decisions, findings, risks, tradeoffs, evidence, knowledge gaps, and open questions. A concern may be missing, partial, or sufficient, with evidence, gaps, and confidence recorded.

The model should distinguish:

- **Methodology state:** domain and process semantics, owned by the harness and shared across agents.
- **Agent state:** agent-specific working or role state.
- **Runtime state:** messages, checkpoints, tool calls, tokens, and other execution mechanics.

Keeping these apart makes it possible to change from a single-agent harness to a planner with specialists and a critic without redefining what counts as progress in the methodology.

## 5. Verifier, checker, and evaluator

**[Reconstructed from retained summary]** The discussion calls for a clear distinction among validation roles:

- A **verifier** checks whether a claim or output is supported by specified evidence or satisfies a rule. It can be narrow and criterion-focused.
- A **checker** is a component or role that checks artifacts, state, or requirements for completeness, consistency, or rule violations. It may use deterministic checks, model judgment, or both.
- An **evaluator** assesses broader quality against success criteria: whether the harness or resulting work achieves the intended outcome. Evaluation can compare behavior and guide redesign.

These labels need not imply three separate agents. They are different responsibilities and may be implemented by one component or several. In Architecture Evaluation, for instance, a checker may flag missing evidence, a verifier may validate that a finding is grounded in cited evidence, and an evaluator may judge overall coverage and usefulness.

## 6. Architecture Evaluation pilot and paper discussion

**[Reconstructed from retained summary]** Architecture Evaluation was discussed as a concrete pilot for grounding the abstractions. It provides a domain in which DomainSpec and Methodology can be distinguished, meaningful methodology state can be modeled, and output criteria can be made observable (evidence-grounded findings, requirement coverage, risks, and tradeoffs).

The pilot should demonstrate the moderate claim: explicit methodology and state can support a useful harness whose realization can be generated or evolved. It should not be presented as proof that HarnessWeaver automatically discovers the best architecture.

**[Reconstructed from retained summary]** The conversation also included discussion of an MDPI paper as relevant prior research or conceptual grounding for the Architecture Evaluation methodology. The retained data available here does not identify the paper’s title, authors, or exact claims; those bibliographic details should be recovered from the original source before citing it. Do not infer a citation from this note alone.

## 7. DeepAgents and runtime independence

**[Reconstructed from retained summary]** DeepAgents was treated as a possible execution/runtime realization, not as the definition of HarnessWeaver. The architectural claim is that HarnessWeaver’s intent, domain knowledge, methodology, and intermediate harness representation should remain conceptually separate from any one runtime. A harness could be materialized with DeepAgents, a skills-based harness, a framework-based application, or a custom runtime where supported.

This is a design goal and distinction, not a claim that all runtime targets are already implemented or interchangeable without adaptation. The paper and diagrams should avoid conflating portability in the representation with completed portability in every backend.

## 8. Comparison with prior art, including `revfactory/harness`

The conversation explicitly warned against claiming “nobody generates harnesses.” It identified `revfactory/harness` as a nearby harness/factory approach and noted its described flow of domain description, control-flow analysis, team architecture selection, generation of agents/skills/orchestration, verification, and evolution, with multiple execution modes and team patterns.

The comparison should therefore position HarnessWeaver relative to existing generators and harness approaches, using verifiable specifics and avoiding unsupported novelty claims. The proposed point of distinction is the explicit treatment of methodology and methodology state as first-class assets, their separation from the harness realization/runtime, and the practical aim of rapid prototyping and evolution before commitment.

Other prior art mentioned in the discussion includes ordinary agent frameworks such as LangChain/LangGraph and harness/skills approaches, plus agent-generation or meta-harness systems. The earlier assistant response also referenced Microsoft Agent Framework and AWS AgentCore as examples of harness/skills infrastructure. These ecosystem descriptions are time-sensitive and should be verified against primary sources before appearing as factual claims in a paper.

### Comparison dimensions proposed in the discussion

| Dimension | Application-first system | Manually specialized harness | Harness generator/factory (e.g. `revfactory/harness`) | HarnessWeaver working position |
|---|---|---|---|---|
| Domain knowledge | Encoded in application code, prompts, tools, retrieval, schemas | Packaged in instructions, skills, tools | Analyzed from input description, depending on system | Explicit domain asset, separated from realization |
| Methodology | Often embedded in workflow/code | Often implicit in instructions and orchestration | May be partly inferred or encoded; compare per system | First-class, explicit process asset |
| Instantiation | Developer builds a custom application | Developer manually adapts an existing harness | Generator creates a harness/team | Rapidly generate or evolve a viable prototype |
| Harness representation | Usually application/framework code | Harness-native files and configuration | Often generated files or target-specific structure | Explicit Harness IR is a design aim |
| Runtime | Framework-specific | Inherited from chosen harness | Depends on supported targets | Conceptually separated from specification; backend support must be demonstrated |
| Methodology state | Application-specific | Often implicit or harness-specific | Compare actual state model | Explicit semantic state maintained by harness and updated by agents |
| Evaluation | Often app-specific testing | Tests/evals may be manual | Verification/evolution capabilities vary | Criteria inform evaluation and prototype evolution |
| Change and commitment | Refactoring after early architectural choices | Manual adaptation | Generated structures may be regenerated/evolved | Lower-cost iteration and progressive commitment |
| Main purpose | Build a domain application | Specialize an existing harness | Generate a team or harness | Prototype and evolve domain-specific harnesses before committing |

This table is a conceptual comparison scaffold. Claims about any named system should be checked against its current documentation, code, and papers before publication.

## 9. The three approaches: figure and table requirements

The user requested a diagram for a paper or slide that shows **three approaches**:

1. Directly build a custom agentic application on a framework.
2. Manually specialize an existing harness with domain skills, tools, and possibly subagents/orchestration.
3. Use HarnessWeaver to represent domain and methodology explicitly, rapidly produce a working harness, then evaluate and evolve it before deciding whether to retain it as a harness or engineer a dedicated application.

**Verbatim retained user instruction:**

> “This position is more moderate and achievable, and also defensible and demostrable through the examples we have. Can you create a diagram for me that illustrates the 3 approaches (1, 2, + Harness Weaver) and their differences, thinking a paper or slide figure. In addition, I could also use a table like the one you mentioned above (including approaches like harness-rev too)”

The user then specified:

> “For the pictures and tables, I´d like also to reflect the aspectos of ‘development speed’ and ‘flexibility to adapt to change’ of the different construction strategies. Keep the chart and the table as different artifacts”

### Required figure

- Present approaches 1, 2, and HarnessWeaver as three distinct paths.
- Show the input (domain problem/expertise, and for HarnessWeaver explicit domain and methodology assets), construction process, and resulting system/prototype.
- Make HarnessWeaver’s evaluation/evolution loop and later choice to retain or graduate the prototype visible.
- Convey **development speed** and **flexibility to adapt to change** for each strategy, with qualitative labels or a carefully explained visual encoding. Do not imply unsupported measured rankings.
- Keep the figure suitable for a paper or slide and do not merge it with the comparison table.
- Do not suggest that HarnessWeaver searches for or discovers an optimal harness. Emphasize faster generation/evolution and delayed commitment.

### Required standalone table

- Compare the same three approaches and include `revfactory/harness` (also referred to in the user request as “harness-rev”) and other relevant prior art where evidence is available.
- Include development speed and flexibility to adapt to change as explicit dimensions.
- Also compare methodology, evaluation, evolution, portability/runtime, representation, and commitment where useful.
- Keep the table as a separate artifact from the figure.
- Qualify claims about named systems and use evidence rather than assuming capabilities.

The last retained assistant response summarized the two artifacts as separate deliverables: a paper/slide figure focused on the three strategies, speed, flexibility, and delayed commitment; and a standalone table including Custom Agentic Application, Harness Specialization, `revfactory/harness`, and HarnessWeaver.

## 10. Current claim boundaries and research direction

The following should be treated as the present, defensible scope:

- HarnessWeaver makes domain knowledge and methodology explicit assets.
- It separates those assets from their particular agentic realization and runtime.
- It supports rapid generation of a viable harness prototype and evaluation-driven evolution.
- It aims to reduce the cost of changing direction and delaying premature commitment.
- Methodology state has domain meaning and persists independently of runtime bookkeeping and agent arrangement.

The following were discussed as future or stronger possibilities, not claims to make about the current system without evidence:

- Systematic autonomous exploration of a large harness design space.
- Automatic discovery of an optimal harness or agent architecture.
- Learning generally applicable architecture-selection rules across many experiments.
- Generator self-improvement or multi-objective optimization.
- Guaranteed methodology-equivalence among different harness realizations.
- Full portability across every runtime.

## 11. Compact summary for future work

HarnessWeaver is best presented as an intermediate engineering abstraction between domain methodology and a committed agentic implementation. Its central practical value is making it cheaper to turn explicit domain and methodology assets into a working harness, inspect and evaluate that prototype, and evolve it as understanding improves. It can complement conventional framework-based application development and manual harness specialization; it does not need to replace them. The initial argument should be demonstrated through the Architecture Evaluation pilot and carefully compared with prior art, including `revfactory/harness`, while keeping the claims modest and evidence-backed.

