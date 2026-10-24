# Claude Model Selection Guide

Choose the model for an agent by four criteria: the work's **complexity, expected duration, required autonomy, and response speed**. The model can be specified in `model:` in the YAML frontmatter of the agent definition file, in the `model` parameter of the `Agent` tool, or in `opts.model` passed to `agent()` in `Workflow`. Leave the reason for the choice as a comment in the agent definition or coordination skill.

## Summary decision table

| Model | Selection criteria | Representative work |
|------|----------|----------|
| **fable** | A long-running, autonomous model that plans by itself from a complex goal and chains several steps through to the final output | High-difficulty reasoning, creative work, agent coordination, very hard work that must be entrusted from planning through long-running execution |
| **opus** | A reasoning-focused model that deeply analyzes specialized, complex problems to reach refined judgments and conclusions | Design and architecture, code generation, complex analysis, cross-verification, creative writing |
| **sonnet** | A general-purpose model that handles most everyday work, such as writing, coding, analysis, and research, in a balanced way | General writing, coding, and research; log parsing; format conversion; static file inspection; running deploy scripts; simple collection |

## 1. Fable

**Main role:** suited to very hard work that must be planned and carried out autonomously over a long period. It doesn't stop at answering a question directly; it understands the goal, plans several steps, and continues through to the final output.

### Work it fits well

**① Long-running work with several connected steps** — use when the work isn't finished with one answer and several tasks must be performed in sequence.
- Market research → competitor analysis → strategy formulation → report writing
- Requirements analysis → service structure design → development plan writing → output production
- Reviewing several documents, then deriving a comprehensive conclusion and an execution plan
- Designing the whole process of a long-term project

What matters is that these are **tasks where the results of earlier steps affect the next steps**, not separate, isolated steps.

**② Reviewing large, complex material** — use when large and complex material such as papers, reports, meeting minutes, and technical documents must be reviewed together. This is the case when not just a summary but the following work is needed.
- Analyzing commonalities and differences across several sources
- Identifying conflicting claims
- Distinguishing key evidence from peripheral information
- Synthesizing a lot of material into one logical output

**③ Turning vague ideas into concrete outputs** — work where, when requirements are not fixed and only a rough idea is given, the model decides the needed details by itself and produces an output.
- Developing the idea "a service with this kind of feel" into a business plan
- Designing the structure and content of a presentation from only a rough topic
- Concretizing an incomplete product idea into a feature list and development plan
- Producing a finished report or content with no draft

Choose it when the **ability to judge and fill in the empty parts** matters more than the ability to follow given instructions as they are.

**④ Problems that need deep reasoning together with planning, coordination, and long-running execution** — Fable doesn't always reason more deeply than Opus. Fable is better suited to problems that need planning, coordination, and long-running execution along with deep reasoning.

### When to choose Fable

- When several steps must be gone through to get the result
- When it is hard for the user to specify every procedure directly
- When the model must plan the order of work by itself
- When a finished output must be produced from vast material
- When a project-level result is needed rather than a short answer

## 2. Opus

**Main role:** a high-performance reasoning model that deeply analyzes and solves hard problems. If Fable suits long-term planning and autonomous execution, Opus suits digging deeply into a problem of fixed scope and analyzing it logically.

### Work it fits well

**① Complex research and analysis** — work that doesn't end with finding information but must evaluate several pieces of evidence to reach a logical conclusion.
- In-depth research on a complex industry or market
- Comparative analysis of several research results
- Evaluating the pros and cons of policies or business strategies
- Analyzing causes and effects based on data and documents
- Writing conclusions that synthesize different perspectives

**② Reviewing long technical documents** — work of reading and understanding documents with many technical terms and complex structure. Software design documents, system architecture documents, research papers, technical specifications, product requirements documents, and complex API and development documents fall into this category. It suits **grasping the logical structure and technical meaning** more than shortening documents.

**③ Reviewing research methodology** — work that examines not only the research results but also whether the methods used to obtain them are valid.
- Checking whether the research design is appropriate, whether the sample is sufficient, and whether the sample is unbiased
- Checking that measurement methods and statistical conclusions have no problems
- Reviewing whether conclusions are exaggerated beyond the actual evidence, and whether there is room for other interpretations

**④ Coding that performs several development steps by itself** — doesn't stop at producing one or two lines of code; it understands the goal and carries out several development tasks in succession.
- Analyzing an existing codebase and searching for the causes of errors
- Code changes across several files, feature implementation, and writing tests
- Improving code structure and judging the next task by itself during development

### When to choose Opus

- When the problem is specialized and hard but **its scope is relatively clear**
- When in-depth logical analysis and review are needed
- When technical documents or papers must be understood accurately
- When flaws in research or analysis must be found
- When complex coding or technical problems must be solved

## 3. Sonnet

**Main role:** a balanced general-purpose model that reliably performs most everyday work. Unless the work is very complex or needs specialized judgment, it can be used broadly for writing, coding, research, and analysis.

### Work it fits well

**① Writing and content production** — suited to emails, blog posts, report drafts, ad copy, proofreading and rewriting sentences, presentation scripts, planning social media content, and brainstorming ideas.

**② General coding work** — suited to writing functions, fixing code errors, developing simple programs, explaining existing code, refactoring, writing test code, and producing data-processing scripts.

**③ Analysis and research** — suited to outlining a topic, comparing products and services, analyzing document contents, simple competitor research, extracting key claims, comparing pros and cons, and organizing analysis results into tables or reports.

**④ Problem solving made up of several steps** — performs work of clear scope by dividing it into several steps. Writing a presentation after summarizing material, making code examples after analyzing requirements, or explaining results after analyzing data fall into this category. Distinguish this from the long-running, autonomous projects entrusted to Fable.

**⑤ Repetitive and operational work** — suited to log parsing, format conversion, static file inspection, running deploy scripts, and simple collection.

### When to choose Sonnet

- Use it when you're not sure which model to choose. If it is hard to judge, make sonnet the default.
- Use it when everyday work must be handled quickly and reliably.
- Use it when performing several kinds of work together, such as writing, coding, and research.
- Use it when dealing with problems that are neither too simple nor overly complex.
- Use it when both speed and result quality must be considered.

## Criteria for distinguishing Fable and Opus

- **Fable**: plans the whole work and carries it out autonomously over a long time.
- **Opus**: reasons and analyzes deeply about a complex problem of fixed scope.

For example, **Opus** suits deeply critiquing one paper, and **Fable** suits reviewing dozens of papers, setting a research strategy, and producing the final report. If the results of earlier steps affect the next steps and the model must chain several steps by itself, use Fable. If one problem of clear scope must be analyzed deeply, use Opus.

## Rules for applying this to a harness

1. **Judge by the work** — don't choose a model for the reason "it's an important agent". Choose the model by weighing the complexity, expected duration, required autonomy, and response speed of the work the agent will handle.
2. **Don't assign the same model in bulk without a rationale** — assigning fable or opus to every agent only increases cost. Choose a suitable model for each agent and leave the reason as a comment.
3. **Distinguish the coordination layer from the execution layer** — even if fable is used for the layer that handles planning and coordination (the main session or a supervisor agent), assign models separately to the worker agents below it to suit each task. Just because the coordinating agent is fable doesn't mean the worker agents must also be fable.
4. **Choose a model per workflow phase** — in a `Workflow` script, a different model can be specified per phase with `opts.model`. Use sonnet for repetitive collection and conversion phases, opus for in-depth verification, judging, and design phases, and fable for phases that set the overall plan and run for a long time.
