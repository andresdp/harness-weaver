# Claude Model Selection Guide

Choose the model for an agent against four criteria: **complexity, expected duration, required autonomy, and response speed**. The model can be set in the `model:` field of the YAML frontmatter in the agent definition file, in the `model` parameter of the `Agent` tool, or in `opts.model` passed to `agent()` in a `Workflow`. Record the reason for the choice as a comment in the agent definition or orchestration skill.

## Quick decision table

| Model | Selection criteria | Representative tasks |
|------|----------|----------|
| **fable** | A long-horizon, autonomous model that plans on its own around a complex goal and chains multiple steps through to the final artifact | High-difficulty reasoning, creative work, agent orchestration, and very hard tasks that must be entrusted from planning through long-horizon execution |
| **opus** | A reasoning-centric model that deeply analyzes professional, complex problems and reaches refined judgments and conclusions | Design and architecture, code generation, complex analysis, cross-verification, writing |
| **sonnet** | A general-purpose model that handles most everyday work — writing, coding, analysis, research — in a balanced way | Ordinary writing, coding, and research; log parsing; format conversion; static file checks; running deployment scripts; simple collection |

## 1. Fable

**Primary role:** Suited to very hard tasks that must be planned and then carried out autonomously over a long horizon. Rather than stopping at a one-shot answer, it understands the goal, plans multiple steps, and sees them through to the final artifact.

### Well-suited tasks

**① Long-horizon work spanning multiple steps** — Use it when a single reply is not enough and several jobs must be performed in sequence.
- Market research → competitor analysis → strategy formulation → report writing
- Requirements analysis → service architecture design → development plan drafting → artifact production
- Reviewing many documents and deriving a synthesized conclusion and action plan
- Designing the full course of a long-term project

What matters is that the individual steps are not separate: **the result of one step influences the next.**

**② Reviewing material that is long and complex** — Use it when a large, complex body of material — papers, reports, meeting minutes, technical documents — must be reviewed together, and the job goes beyond simple summarization to producing the next deliverable.
- Analyzing commonalities and differences across many sources
- Identifying claims that conflict with each other
- Separating core evidence from peripheral information
- Synthesizing a large body of material into one coherent artifact

**③ Turning a vague idea into a concrete artifact** — When requirements are not settled and only a rough idea is given, this is work where the model decides the necessary details itself and produces the artifact.
- Developing an "a service that feels like this" idea into a business plan
- Designing the structure and content of a presentation from only a rough topic
- Concretizing an incomplete product idea into a feature list and development plan
- Producing a finished report or content from a state with no draft

Choose it when the ability to **judge and fill in the blanks** matters more than the ability to follow fixed instructions verbatim.

**④ Problems that need deep reasoning together with planning, coordination, and long-horizon execution** — Fable does not unconditionally reason more deeply than Opus. Fable is the better fit for problems that require planning, coordination, and long-horizon execution alongside deep reasoning.

### When to choose Fable

- When reaching a result requires going through multiple steps
- When it is hard for the user to specify every procedure by hand
- When the model must plan the order of work itself
- When a finished artifact must be built from a large body of material
- When you need a project-scale result rather than a short answer

## 2. Opus

**Primary role:** A high-performance reasoning model that deeply analyzes and solves hard problems. Where Fable fits long-horizon planning and autonomous execution, Opus fits digging deeply into a well-scoped problem and analyzing it logically.

### Well-suited tasks

**① Complex research and analysis** — Work that does not stop at finding information but must weigh multiple pieces of evidence and reach a logical conclusion.
- Deep investigation of a complex industry or market
- Comparative analysis of multiple research results
- Evaluating the pros and cons of a policy or business strategy
- Analyzing cause and effect from data and documents
- Writing conclusions that synthesize differing perspectives

**② Reviewing long technical documents** — Reading and understanding documents dense with specialized terminology and complex structure. Software design documents, system architecture documents, research papers, technical specifications, product requirement documents, and complex API or development docs fall here. It fits **grasping the logical structure and technical meaning** rather than shortening the document.

**③ Reviewing research methodology** — Examining not just the results but whether the method that produced them is sound.
- Checking whether the study design is appropriate, the sample is large enough, and the sample is free of bias
- Checking the measurement approach and statistical conclusions for flaws
- Reviewing whether conclusions overstate the actual evidence or admit a different interpretation

**④ Coding that performs multiple development steps on its own** — Rather than producing a line or two of code, it understands the goal and performs several development tasks in sequence.
- Analyzing an existing codebase and locating the cause of defects
- Modifying code across multiple files, implementing features, writing tests
- Improving code structure and deciding the next task on its own during development

### When to choose Opus

- When the problem is specialized and hard but its **scope is fairly clear**
- When deep logical analysis and review are needed
- When a technical document or paper must be understood precisely
- When gaps in research or analysis must be found
- When a complex coding or technical problem must be solved

## 3. Sonnet

**Primary role:** A balanced general-purpose model that reliably handles most everyday work. Unless a task needs highly complex or specialized judgment, it serves broadly for writing, coding, research, and analysis.

### Well-suited tasks

**① Writing and content production** — Suited to email, blog posts, report drafts, ad copy, proofreading and rewriting, presentation scripts, social media content planning, and ideation.

**② Ordinary coding work** — Suited to writing functions, fixing code defects, building simple programs, explaining existing code, refactoring, writing test code, and creating data-processing scripts.

**③ Analysis and research** — Suited to outlining a topic, comparing products or services, analyzing document contents, simple competitive research, extracting key claims, weighing pros and cons, and organizing analysis results into tables or reports.

**④ Multi-step problem solving** — Carries out clearly scoped work divided into several steps. Summarizing material and then writing a talk, analyzing requirements and then producing a code example, or analyzing data and then explaining the results all fall here. Distinguish this from the long-horizon autonomous projects you delegate to Fable.

**⑤ Repetitive and operational work** — Suited to log parsing, format conversion, static file checks, running deployment scripts, and simple collection.

### When to choose Sonnet

- Use it when you are not sure which model to pick. If the call is hard to make, default to sonnet.
- Use it when everyday work must be handled quickly and reliably.
- Use it when several kinds of work — writing, coding, research — must be performed together.
- Use it when the problem is neither too simple nor excessively complex.
- Use it when both speed and result quality matter.

## Criteria that separate Fable from Opus

- **Fable**: plans the whole job and executes autonomously over a long horizon.
- **Opus**: reasons deeply and analyzes a complex problem with a fixed scope.

For example, critically reviewing a single paper in depth suits **Opus**, while reviewing dozens of papers, setting a research strategy, and producing the final report suits **Fable**. If earlier steps influence later ones and the model must chain the steps together on its own, use Fable. If you must analyze one clearly scoped problem in depth, use Opus.

## Harness application rules

1. **Judge by the work** — Do not choose a model on the grounds that "this is an important agent." Weigh the complexity, expected duration, required autonomy, and response speed of the work the agent will take on, and choose accordingly.
2. **Do not assign one model wholesale without justification** — Assigning fable or opus to every agent only inflates cost. Pick the right model per agent and record the reasoning as a comment.
3. **Separate the orchestration layer from the execution layer** — Even if the layer responsible for planning and coordination (the main session or a supervisor agent) uses fable, assign each underlying worker agent the model that fits its own work. An orchestration agent being fable does not mean the worker agents must be fable too.
4. **Choose a model per workflow stage** — In a `Workflow` script, `opts.model` lets you specify a different model per stage. Use sonnet for repetitive collection and transformation stages, opus for deep verification, judging, and design stages, and fable for the stage that plans the whole effort and executes over a long horizon.
