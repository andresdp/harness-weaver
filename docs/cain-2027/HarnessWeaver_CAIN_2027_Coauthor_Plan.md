# HarnessWeaver: Towards Rapid Prototyping of Software Architecture Assistants

**Co-author project plan — CAIN 2027 Research Track, short research paper**  
**Status:** proposed framing and work plan; all expected benefits below require evidence.  
**Planning date:** 24 October 2026. **Submission deadline:** 30 October 2026 (AoE, UTC−12); this is a six-day sprint. The CAIN CFP allows short research papers up to **5 pages plus 2 pages of references** and explicitly welcomes research-oriented position/new-idea papers that may not yet be fully evaluated. [CAIN 2027 Research Track CFP](https://conf.researchr.org/track/cain-2027/cain-2027-call-for-papers)

## 1. Paper purpose and positioning

### Proposed thesis

Domain-specific agentic systems are commonly built either as bespoke applications, with architecture encoded directly in framework code, or by manually specializing a general-purpose agent harness with skills, subagents, tools, and orchestration instructions. HarnessWeaver proposes an intermediate engineering layer that represents intent, domain knowledge, and methodology explicitly, then generates and evolves a runtime-specific harness from a shared specification. The aim is to support rapid prototyping and **progressive commitment**: defer runtime and implementation choices where practical, then commit when a runnable realization is needed.

This is a proposed engineering approach and feasibility argument. The paper must not claim that HarnessWeaver finds an optimal harness, searches the full design space, or has already shown lower development cost or better assistant quality. Those are future empirical questions.

### Construction strategies to compare

| Strategy | What is specified directly | Typical trade-off to investigate |
|---|---|---|
| Bespoke agentic application | Agents, workflows, state, tools and runtime in application/framework code (e.g., LangChain/LangGraph or comparable frameworks) | Direct control; domain logic and runtime decisions may become coupled |
| Manual specialization of a general harness | Skills, agent/subagent definitions, prompts, tools and orchestration configuration | Fast access to existing harness capabilities; configuration and domain assets may be hand-maintained and runtime-specific |
| HarnessWeaver (proposed) | Intent, domain, methodology and a runtime-neutral HarnessSpec/IR, then adapters/materializers | Intended intermediate layer for reuse, generation and evolution; benefits remain to be measured |

Frame early commitment and adaptation cost as **motivating concerns**, not established universal facts. Use examples and related work to motivate them; do not imply all implementations suffer equally.

## 2. Related approaches and conceptual antecedents

The paper should position HarnessWeaver among related ideas rather than claim an empty space:

| Approach | Relevance to HarnessWeaver | Careful distinction |
|---|---|---|
| **MetaGPT and SOP-driven multi-agent systems** | Shows how standard operating procedures, role specialization, intermediate artifacts, and multi-agent coordination can encode a method of work. | Methodology-driven agent collaboration is an antecedent; HarnessWeaver's proposed focus is an explicit methodology model separated from runtime realization and materializable to different harnesses. Cite the original MetaGPT paper. |
| **Claude Skills / general-harness specialization** | Skills, subagents, tools and orchestration let users configure general-purpose agent harnesses for domains. | Usually a target realization or manually authored configuration surface, not evidence by itself of a runtime-neutral generation layer. Cite official Claude Code docs for the exact features discussed. |
| **`revfactory/claude-code-harness` paper** | Reports a controlled author-run study of structured preconfiguration for coding-agent output quality. It supports the plausibility that a preconfigured harness can matter. | The reported result concerns coding tasks and a particular setup; it does not establish HarnessWeaver's claims or the general benefit of harness generation. Treat as prior evidence, not a result to generalize. |
| **`revfactory/harness`** | Close prior art for generating and evolving a domain-specific agent team/harness, with orchestration patterns. Its patterns can inform the initial orchestration design. | Compare directly on inputs, intermediate representation, generated assets, runtime assumptions, and evolution loop. Identify overlap honestly; articulate HarnessWeaver's distinctive explicit Methodology and runtime adapter boundary only if implemented. |
| **DeepAgents** | Initial executable target for a YAML-driven HarnessSpec adapter; provides native skills, subagents and task/delegation mechanisms. | DeepAgents is an initial runtime, not the definition of HarnessWeaver. Its current APIs and capabilities must be checked against official docs and pinned in the artifact. |

Primary links: [MetaGPT paper](https://arxiv.org/abs/2308.00352), [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills), [Claude Code subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents), [`revfactory/claude-code-harness` paper and repository](https://github.com/revfactory/claude-code-harness), [`revfactory/harness`](https://github.com/revfactory/harness), [DeepAgents documentation](https://docs.langchain.com/oss/python/deepagents/overview). Verify bibliographic details and current API behavior before submission.

The harness paper/repository reports an author-run controlled A/B on 15 software-engineering tasks (mean quality 49.5 to 79.3 in the repository summary). If included, state the sample, coding-task scope, author-run nature, and source; do not present this as independent confirmation or transfer it to architecture evaluation.

## 3. HarnessWeaver concepts and boundaries

Proposed conceptual flow:

```text
IntentSpec + DomainSpec + Methodology
                  │
                  ▼
         HarnessWeaver generator
                  │
                  ▼
            HarnessSpec / IR
                  │
            runtime adapter
           ┌──────┴──────┐
           ▼             ▼
      Claude harness  DeepAgents harness
           └──────┬──────┘
                  ▼
         execute → check/evaluate → evolve
```

- **IntentSpec:** user/stakeholder goal, scope, constraints, expected outcomes, and intended interaction boundary.
- **DomainSpec:** domain concepts, relations, vocabulary, rules, knowledge sources, and domain-specific constraints.
- **Methodology (first-class):** activities and their ordering/conditions; techniques; inputs and outputs; artifacts; readiness/precondition criteria; validation criteria; and completion conditions. It may include **methodology/domain-semantic state** such as current activity, accumulated architecture decisions, rationale, unresolved questions, evidence, and artifact status.
- **HarnessSpec / IR:** runtime-neutral description of agents/roles, skills/capabilities, tool requirements, orchestration, state bindings, and generation metadata. Keep only distinctions needed to render or execute the pilot; avoid speculative schema breadth.
- **Runtime adapter/materializer:** maps the shared specification to a target runtime's native files and constructs; reports unsupported features and any lossy mappings.
- **Evaluation/evolution:** checks generated assets and execution artifacts, records gaps, and supports human-directed changes to source specifications or realizations. Any automatic optimization or self-learning is out of scope.

**State distinction:** methodology state captures progress and semantic work products in the architecture-evaluation method. Runtime/agent state captures execution details such as messages, tool calls, task delegation, checkpoints, or context. A runtime may store methodology state, but the concepts and ownership should remain distinct in the model.

**Checker, verifier, evaluator:** use these terms deliberately. A *checker* applies a specified rule to an artifact or state (e.g., required fields present). A *verifier* assesses whether a stated condition/invariant holds, ideally with an explicit evidence trail. An *evaluator* judges quality against criteria, potentially with human or model judgment. The pilot should state which is deterministic, which is model-assisted, and which requires human review; do not imply a quality guarantee from a checker.

## 4. Orchestration plan

For the first DeepAgents adapter, use a YAML HarnessSpec as the macro-level source and implement only a small set of orchestration primitives:

- **Sequence:** ordered activities with explicit hand-off artifacts.
- **Parallel:** independent tasks with a defined join/merge point.
- **Delegate:** assign a task to a named role/subagent with explicit inputs and expected outputs.
- **Loop:** repeat a bounded activity while an explicit readiness, validation, or completion condition is unmet; include a maximum/exit policy.

Compile named patterns (pipeline, fan-out/fan-in, producer-reviewer, and supervisor/expert pool) from these primitives only when the case needs them. Macro orchestration comes from generated YAML; DeepAgents executes with its native skills, subagents, and task mechanisms. The adapter should translate and validate orchestration rather than emulate every runtime feature. Record unsupported constructs and manual interventions.

## 5. CAIN fit and scope

The contribution is **AI engineering / software engineering for agentic systems**, especially architecture, lifecycle evolution, reuse, and quality assurance beyond coding agents. Architecture Evaluation is the case study used to make the engineering approach concrete; **AI4SE is not the main contribution**. The CAIN CFP explicitly highlights engineering principles, architecture, and quality assurance for agentic software, especially beyond coding agents, and accepts preliminary or not-yet-fully-evaluated work in the 5+2 short-paper category.

**Deadline context:** CAIN lists Friday 30 October 2026, AoE (UTC−12). Confirm the HotCRP submission details and formatting instructions on submission day. The deadline is firm according to the CFP. At the planning date, the team has six calendar days.

## 6. Initial validation plan

### Minimum viable matrix: one domain × two runtimes

Take **Architecture Evaluation** as one shared domain/methodology source and generate/materialize two harnesses:

1. Claude-oriented realization using skills, subagents, and orchestration/configuration files.
2. DeepAgents realization using native skills, subagents/task mechanisms, and the DeepAgents adapter.

This is a **feasibility demonstration of cross-runtime materialization and separation**, not a controlled performance or assistant-quality evaluation. The central observable question is whether the same domain and methodology assets can be carried across both realizations with explicit, reviewable mapping.

Document for each target:

- shared source assets and runtime-specific generated files;
- mapping from each source concept to target construct, including unsupported/lossy mappings;
- generated file inventory, versions, and reproducible invocation/configuration;
- manual corrections, interventions, and their reasons (distinguish required from optional polish);
- implementation effort and change footprint, with a consistent recording method (person-hours, files/lines touched, and categories of change; report observed values only);
- a small set of representative end-to-end architecture-evaluation activities and their resulting artifacts/checks;
- whether the same methodology/state and validation conditions remain interpretable in both runtimes.

### Stretch: two domains × two runtimes

If the minimum matrix is stable and time remains, add **Architecture Design** (e.g., SARA or a suitably available method) in both runtimes. This supports an exploratory look at both horizontal/runtime flexibility and domain flexibility. Do not let this stretch displace reliable packaging and documentation of the minimum case.

### Exploratory research questions

- **RQ1 (feasibility):** Can HarnessWeaver generate executable architecture-assistant harnesses from explicit intent, domain, and methodology specifications?
- **RQ2 (runtime flexibility):** Which domain and methodology assets can be reused across Claude and DeepAgents realizations, and what adaptation is required?
- **RQ3 (optional, if second domain):** Which parts of the representation and adapters generalize across Architecture Evaluation and Architecture Design?

These are exploratory questions for a short paper. Future empirical RQs can study development effort, adaptation cost, assistant quality, maintainability/evolvability, and the effect of iterative generation. Do not claim speed/flexibility without measurement and a clear baseline.

## 7. Implementation plan

Prioritize in order. Stop at the minimum viable artifact if the schedule requires it.

| Priority | Work item | Deliverable / completion criterion |
|---|---|---|
| **Must** | Freeze the pilot method and architecture-evaluation example | A bounded activity flow, inputs/outputs, artifacts, readiness/validation/completion criteria, and representative example inputs. |
| **Must** | Define minimal YAML schemas for IntentSpec, DomainSpec, Methodology, and HarnessSpec | Versioned schemas plus one valid, documented instance; reject malformed required fields with useful diagnostics. |
| **Must** | Model methodology state separately from runtime state | Schema/example identifying activity progress, semantic state, evidence/artifact status, and runtime execution data separately. |
| **Must** | Implement a small generator from shared assets to HarnessSpec | Deterministic generation for the pilot; record generated files and source-to-output traceability. |
| **Must** | Implement Claude materializer | Produce runnable/documented skills, subagents, and orchestration configuration for the chosen Claude harness; mark manual setup and unsupported mappings. |
| **Must** | Implement DeepAgents runtime/orchestration adapter | Load YAML HarnessSpec, validate it, map Sequence/Parallel/Delegate/Loop used by the case to native mechanisms, and expose unsupported mappings. |
| **Must** | Add checks/evaluators for the pilot artifacts | At least structural/schema checks and explicit methodology-specific checks; identify human/model judgments separately. |
| **Must** | Package reproducible examples | One-command or clearly documented generation and launch instructions, dependency/runtime versions, example inputs, output inventory, and limitations. |
| **Stretch** | Add named orchestration pattern compilation | Add only patterns exercised by the case, with mapping examples and exit behavior. |
| **Stretch** | Add Architecture Design/SARA domain | Second domain assets plus mappings/materializations to both runtimes. |
| **Stretch** | Add evolution workflow | Demonstrate a small source-spec change and regenerate both targets; report changed assets and any manual repair. |

## 8. Validation evidence, tables, and limitations

Collect evidence during implementation; do not reconstruct effort or interventions from memory at the end.

**Suggested evidence package:** versioned source specs; generator/adapter versions; generated file trees; mapping notes; execution transcripts or structured logs with sensitive data removed; representative methodology artifacts; checker outputs; a dated intervention log; effort/change log; and instructions sufficient for a co-author to reproduce the generation.

**Paper tables/figures:**

1. **Figure 1 — Three construction strategies:** bespoke app, manual general-harness specialization, HarnessWeaver intermediate layer. Show the shared domain/methodology inputs and different commitment points.
2. **Compact related-approach comparison table:** compare unit of specification, methodology representation, generation/evolution, runtime scope, orchestration, and evidence. Populate from cited sources and inspected artifacts; use “not reported/not assessed” rather than unsupported negatives.
3. **Validation matrix table:** domain × runtime, shared inputs, generated outputs, runnable status, manual interventions, and checks performed.
4. Optional compact **effort/change table:** person-hours and touched/generated files by phase and runtime, with definitions and caveat that this is descriptive pilot data, not a controlled comparison.

**Threats and limitations to state:** one domain and two runtimes provide narrow evidence; one implementation/team can bias effort estimates; generated files and manual polishing complicate attribution; runtimes differ in capabilities and APIs; model nondeterminism can affect executions; Claude/DeepAgents versions may change; an executable harness does not establish useful or correct architecture advice; architecture-evaluation criteria may be incomplete; checker coverage is not a quality guarantee; and close prior art may overlap. Mitigate through transparent provenance, fixed versions, explicit intervention logs, shared test inputs, and restrained claims. The pilot can establish feasibility and expose mapping costs, not comparative superiority.

## 9. Five-page paper plan

IEEE conference format; target **five pages of paper plus references (maximum two pages)**. Adjust after drafting and confirm whether figures count in the main page limit per the CFP/template.

| Section | Approx. pages | Content |
|---|---:|---|
| 1. Introduction and motivation | 0.75 | Problem, three construction strategies, thesis, contributions, and CAIN relevance. Introduce Figure 1. |
| 2. Related approaches | 0.65 | MetaGPT/SOP methods, manual harness specialization, harness evidence, `revfactory/harness`, DeepAgents. Include compact comparison table. |
| 3. HarnessWeaver approach | 1.35 | Intent/Domain/Methodology, HarnessSpec/IR, state boundaries, adapter, orchestration, checker/verifier/evaluator distinctions. |
| 4. Architecture Evaluation feasibility case | 1.15 | Methodology, one-domain/two-runtime setup, generation process, mapping and intervention evidence, validation matrix. |
| 5. Discussion and research agenda | 0.80 | What feasibility suggests, limitations, empirical questions, evolution and broader domain/runtime agenda. |
| 6. Conclusion | 0.30 | Concise claim and next research step. |
| **Total** | **5.00** | References up to two additional pages. |

Keep implementation detail that does not support the central argument in the artifact repository. The paper's primary contribution is the engineering abstraction and its feasibility illustration, not a catalogue of every planned feature.

## 10. Writing and submission work plan

Given the 30 October deadline, run these as short phases with explicit daily checkpoints; assign owners in the placeholders below during the co-author meeting.

| Phase | Target timing | Actions | Owner(s) |
|---|---|---|---|
| A. Freeze claim and scope | 24 Oct | Agree thesis, minimum matrix, exact pilot method, terminology, and which claims are demonstrated vs proposed. | Lead: **[name]**; co-authors: **[names]** |
| B. Freeze schemas and case | 24–25 Oct | Complete minimal schemas, Architecture Evaluation source assets/state, representative inputs, and validation criteria. | Implementation: **[name]**; method/domain review: **[name]** |
| C. Materialize both runtimes | 25–27 Oct | Generate Claude and DeepAgents outputs; run representative activities; record failures, manual interventions, effort, versions, and artifacts. | Claude path: **[name]**; DeepAgents path: **[name]** |
| D. Consolidate evidence and draft | 27–28 Oct | Populate mapping/validation tables; create Figure 1; draft all sections and references; ensure claims track evidence. | Evidence: **[name]**; writing lead: **[name]** |
| E. Review and revise | 29 Oct | Co-author review for novelty/related work, technical accuracy, reproducibility, CAIN fit, anonymous submission, and page limits. Resolve all comments. | All; integrator: **[name]** |
| F. Finalize and submit | 30 Oct (AoE deadline) | Format in IEEE template, verify figures/citations/anonymity, upload manuscript and any required metadata/artifact links, submit with time buffer, confirm receipt. | Submission owner: **[name]** |

### Submission checklist

- [ ] Short-research framing and a single, bounded contribution are clear in title, abstract, introduction, and conclusion.
- [ ] The paper says **proposed**, **expected**, or **future work** where claims are not validated; all reported measurements have a method and provenance.
- [ ] Architecture Evaluation is presented as the case study; the main contribution is agentic-software engineering, not AI4SE.
- [ ] The minimum one-domain/two-runtime matrix is complete, or any incomplete cell is explicitly disclosed.
- [ ] Related-work comparison acknowledges MetaGPT, skills/manual specialization, the harness paper, `revfactory/harness`, and DeepAgents with precise scope.
- [ ] Generated files, runtime versions, manual interventions, effort/change footprint, and checks are documented.
- [ ] Figure 1 and compact comparison/validation tables fit and remain readable in IEEE two-column format.
- [ ] Limitations and threats are explicit; no claim of optimal search, general superiority, or measured speed without evidence.
- [ ] IEEE template, five-page body limit, reference allowance, double-anonymous review, and artifact anonymity are checked against CFP instructions.
- [ ] Submission is uploaded before 30 October 2026 AoE and receipt/status is verified.

## 11. Scope freeze

For this submission, do not add automatic optimal-harness discovery, large design-space exploration, generator self-learning, or elaborate multi-domain evaluation unless already implemented and reproducible. Do not expand the schema beyond the pilot's needs. Keep Architecture Design/SARA as a stretch goal. The paper should make a modest, reviewable argument: **an explicit domain-and-methodology layer can be used to produce more than one runtime realization of an architecture assistant, and the pilot documents what is shared, what changes, and what manual work remains.**
