---
name: harness
description: "Designs or updates task-specific agent harnesses from project and domain context. Use when the user asks to build, set up, design, extend, audit, or maintain a harness or agent team. Use HarnessSpec for reusable or complex harnesses; a simple one-off may proceed without a saved spec when the spec would add more overhead than value. Materialize only supported runtime forms and report unsupported capabilities. For retrospectives and applying execution feedback, use the evolve skill."
---

# Harness v2 — Designing Agent Teams and Skills

This skill defines the shared harness-design method and currently emits Claude Code artifacts when that runtime is selected. Build or update the HarnessSpec before runtime artifacts for reusable or complex work; use `deepagents-port` for the DeepAgents form and report unsupported requirements. Do not present Claude-specific steps below as portable runtime behavior.

Design a harness tailored to the project. Define each agent's role, and create the skills agents follow while doing their work.

## Core principles

1. Agents describe *who* does the work; skills describe *how* the work is done. Choose the runtime before writing runtime-specific files, and do not put Claude paths into a different runtime's artifacts.
2. Choose an execution mode based on the workflow. If ordering and loop conditions can be defined in code, coordinate with a workflow. If you need to exchange feedback with the same specialists, use persistent agents. For work where you only need a one-time result, delegate to sub-agents. Detailed selection criteria are covered in step 2.
3. Pick models to match the task's complexity, duration, autonomy, and response-speed needs. Use fable for the hardest work requiring long-running autonomous planning and execution, opus for design, code generation, complex analysis, and cross-checking, and sonnet for routine work like log analysis, format conversion, and simple collection. Detailed criteria are covered in step 3.
4. Record only the trigger conditions and change history in `CLAUDE.md`, so the orchestrator skill can be invoked in new sessions too.
5. Continuously feed what is learned from execution results back into agents, skills, and `CLAUDE.md`. The `evolve` skill handles retrospectives and detecting changes.
6. Write generated agent definitions, skills, orchestrators, and `CLAUDE.md` entries in the language the user writes in the conversation. Just because this skill document and the templates in `references/` are written in one language, do not write the artifacts in that language by default. Translate template headings and example phrasing into that user's language as well. If the user specifies a language, follow it; when extending an existing harness without a language specified, follow the language of the existing files.
7. Use HarnessSpec as the explicit shared design for reusable or complex harnesses. Keep it compact. A simple one-off may be prototyped without a saved spec when the spec would take more effort than the experiment; state that choice and its tradeoff.
8. Separate shared harness intent from runtime implementation. Generate only a runtime form that the selected adapter supports, and disclose any unsupported capability or meaning lost in translation.
9. Make the generated Harness IR explain the work's intent, domain method, required evidence, and meaning of progress. Runtime counters, agent messages, retries, and task completion flags do not prove that domain work is ready or complete.

## Resolve the design inputs

Before choosing roles or runtime artifacts, inspect the supplied request and project materials for four distinct inputs:

| Input | Record |
|---|---|
| **Intent** | Goal, scope, exclusions, users, and the decision or outcome the work should support. |
| **Domain knowledge** | Relevant skills, standards, examples, schemas, project constraints, authority, revision, and provenance. Keep references to sources; do not silently replace or duplicate them. |
| **Methodology** | The domain procedure, its source, required activities, decision criteria, and any HarnessWeaver adaptation. Distinguish this from the general method for designing a harness. |
| **Runtime constraints** | Target runtime, supported coordination and interaction features, persistence, tool access, and materialization limits. Keep these out of domain-method claims. |

Surface conflicts, assumptions, and missing evidence in the design record. Mark unknown or not-provided inputs explicitly; do not promote an inference into a source fact. If no recognized method is supplied, state the proposed procedure and label it as a design choice that needs review.

For a reusable or complex workflow, create or update a compact HarnessSpec before materializing runtime artifacts. A lightweight brief in the conversation is sufficient for a simple, bounded one-off when a saved spec would cost more than it adds; record the choice and the tradeoff. Use the repository's canonical schema when available, and preserve source references and revisions.

## Harness IR content

Generate an inspectable, runtime-neutral design record with these semantic parts, whether represented in a HarnessSpec or a concise brief:

- **Intent and methodology:** goal, scope, domain method and versioned sources, plus labeled adaptations.
- **Activities and readiness:** ordered or otherwise related activities, responsible roles, inputs, outputs, and evidence-based prerequisites for starting each activity.
- **Artifacts and validation:** expected artifacts and their contracts, plus checks that verify structure, content, provenance, and evidence links. Keep checker responsibility clear; it may be performed by the producer, a verifier, or deterministic code when risk and repeatability justify it. Do not require a separate agent by default.
- **Semantic progress and completion:** domain-defined states or checkpoints, evidence supporting each assessment, unresolved gaps, next-state requirements, and explicit completion criteria. Execution bookkeeping can be included separately when useful, but cannot update semantic progress by itself.
- **Evidence and uncertainty:** source and artifact references for claims; distinguish observed facts, assumptions, unknowns, conflicts, and accepted gaps.
- **Runtime realization:** selected runtime form and supported mappings. Report any unsupported capability or change in meaning rather than implying equivalent behavior.

Validation, verification, and evaluation have different jobs: validation checks the design and artifact contracts; verification checks whether a produced artifact meets a stated requirement; evaluation judges quality or usefulness against declared criteria. They may share a person or tool, but keep their questions and results distinguishable.

## Procedure

### Step 0: Check the current state

When the harness skill is invoked, first inspect the existing configuration.

1. Read `project/.claude/agents/`, `project/.claude/skills/`, and `project/CLAUDE.md`.
2. Choose the procedure based on the current state.
   - **Fresh build**: if the agent or skill directories don't exist or are empty, run everything from step 1.
   - **Extend existing configuration**: to add agents or skills to an existing harness, run only the steps needed from the table below.
   - **Operate/maintain**: to inspect, fix, or sync an existing harness, go to the operations procedure in step 7.

   | Change | Step 1 | Step 2 | Step 3 | Step 4 | Step 5 | Step 6 |
   | --- | --- | --- | --- | --- | --- | --- |
   | Add an agent | Skip; use the step 0 findings | Decide which execution mode, team, and phase to place it in | Required | When a dedicated skill is needed | Update the orchestrator | Required |
   | Add/modify a skill | Skip | Skip | Skip | Required | When wiring changes | Required |
   | Change structure/execution mode | Skip | Required | Only affected agents | Only affected skills | Required | Required |

3. If an existing orchestrator contains `TeamCreate`, `TeamDelete`, or `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, it is a v1 artifact. It won't work in the current runtime, so propose moving it to v2. Follow the details in the "Migrating from v1 to v2" section of `references/execution-modes.md`.
4. Compare the actual agent/skill lists against the `CLAUDE.md` entries and find mismatches.
5. Read `project/CLAUDE.md` for pointers, but treat it as context — the authoritative state is always the files on disk.
6. Report the inspection findings and the execution plan to the user and get confirmation.

### Step 0-1: Clarification and option gates (human-in-the-loop)

Deriving agents and skills is a design task, not a transcription task. The description the user gives is never complete. **Ask before writing files — don't guess and hope the user corrects you later.** Two kinds of gates, both run against the user directly (this conversation), never delegated to a sub-agent:

**Clarification gate — run after step 1 (domain analysis), before step 2:**

1. List what the request left ambiguous: scope boundaries, terminology conflicts, missing volume/scale inputs, target consumers of the artifacts.
2. For each, either resolve it from evidence you can read (codebase, existing harness files — say which) or **ask the user**. Batch related questions; don't interrogate one at a time.
3. Record the answers as design constraints in the plan you present.

**Option gate — run at the two highest-leverage decision points:**

1. **Execution mode + team shape** (end of step 2): present 2–3 viable compositions (e.g. workflow vs. persistent agents vs. hybrid; producer-reviewer vs. expert pool) with the trade-offs and your recommendation, and let the user pick. Never silently choose a mode that changes cost profile or collaboration style.
2. **Artifact contracts** (during step 4, before writing skills): when multiple defensible JSON/file structures exist — or when a downstream consumer already pins them — show the proposed contract (filenames + top-level fields + ID-linkage) and get a yes before generating all skills against it.

Gate discipline:

- Gates are mandatory for **fresh builds**; for extensions of an existing harness, gate only on what the change touches.
- Prefer concrete artifacts over prose at every gate: show the proposed stage list, the artifact table, or a sample skill skeleton — the user reacts to something reviewable.
- If the user is unavailable or says "just proceed", proceed with your recommendation, but write the decisions (and that they were unconfirmed) into the CLAUDE.md change history so the `evolve` skill can revisit them.
- Never use a gate to offload a judgment the skill itself mandates (model tiering, verification patterns) — those are the factory's job; gates are for choices that genuinely belong to the user.

### Step 1: Analyze the domain and the work

1. Identify the project's domain and goals from the user's request.
2. Break down the kinds of work needed: generation, verification, editing, analysis, and so on.
3. Examine the workflow so an execution mode can be chosen.
   - Can the items to process be enumerated in advance? E.g., migrate N files, review from M perspectives
   - Is an iterate-verify-fix loop needed for the outputs?
   - Do agents need to exchange opinions to get good results?
   - Must you keep talking with the same specialist within one session?
4. Find overlaps or conflicts with the existing agents and skills found in step 0.
5. Look through the codebase to identify the tech stack, data models, and major modules.
6. Match the depth of explanations to the user's vocabulary and question level. Don't use terms like assertions or JSON Schema unexplained with a user who has little coding experience.
7. Look for an existing HarnessSpec or a recorded spec reference. For a new design, decide whether a saved spec earns its cost: multi-stage work, repeat use or evolution, multiple runtime forms, or meaningful evaluation/provenance are signs it does. For a simple one-off, keep the design lightweight and do not force a spec artifact.

### Step 2: Design the execution mode and team structure

#### 2-0. Resolve HarnessSpec and target runtime

1. If the project supplies a HarnessSpec, read it before proposing structural changes. Preserve its domain sources and authority; identify conflicts instead of silently rewriting them.
2. For reusable or complex harnesses, create or update a compact HarnessSpec before materializing runtime files. Use the repository's canonical schema and example when available. Include source references and authority, roles, stages, inputs/outputs, verification, human gates, and runtime requirements. Link to long domain guidance instead of copying it into the spec.
3. Keep a simple one-off light. If the user wants to try it without a saved spec, record that choice in the response and continue with the minimum context needed for a safe harness.
4. Ask which runtime form to generate when the choice changes the artifacts and the user has not specified one. If a spec supports several forms, let the user choose; do not claim that two adapters are equivalent unless both implement the same declared behavior.
5. Validate a saved spec with `hw validate` when the validator is available. In the HarnessWeaver repository, run it through the `harness` Conda environment (`conda run -n harness hw validate <spec-path>`). If no validator is available, report that validation was not run; do not claim the spec passed.
6. Record adapter limitations in a separate fidelity report or in the handoff. Do not add runtime-specific syntax to the shared spec to hide a limitation.

#### 2-1. Choosing an execution mode

Harness v2 uses three Claude Code multi-agent capabilities. Pick one of the following modes to match the workflow.

| Execution mode | Capabilities used | Suited work |
| --- | --- | --- |
| **Workflow orchestration** | `Workflow` script's `agent()`, `pipeline()`, `parallel()`, `phase()` | Work where the item list, verification procedure, and iteration count can be defined in code. Work that needs schema-conforming results or dozens or more `Agent` calls |
| **Persistent agent collaboration** | `Agent(name:)`, `SendMessage`, `TaskCreate`, `TaskUpdate` | Work where named specialists must iterate on feedback, negotiation, and co-editing while keeping conversational context |
| **Sub-agent delegation** | A single `Agent` call; runs in the background by default, parallel calls possible | Work where agents don't need to talk to each other and you only need the result once |

Decide in this order:

1. If the item list, verification criteria, and loop conditions can be expressed in code up front, use a workflow. Don't leave a fixed flow to the model's in-the-moment judgment if you want reruns to behave the same way.
2. If it's hard to define in code and agents must converse or remember earlier context, use persistent agents.
3. If neither applies and you only need the result, delegate to sub-agents.
4. If the nature of the work differs per phase, compose a hybrid mode. Note each phase's execution mode in the orchestrator.

Using the `Workflow` tool requires explicit user consent. Consent is assumed if the user directly requested a workflow run or invoked an orchestrator skill that instructs `Workflow` calls. Keep the default execution to a few agents; scale up only when the user asks for a broad investigation with words like "thorough" or "exhaustive".

> For a comparison of execution modes, concurrency limits, schemas, token budgets, and resume conditions, see `references/execution-modes.md`.

#### 2-2. Choosing a team composition

1. Divide the work by specialty.
2. Choose the composition that fits the work from the six patterns below. Detailed criteria are in `references/team-patterns.md`.
   - **Pipeline**: each stage consumes the previous stage's output in order. A good fit for `pipeline()`.
   - **Fan-out/Fan-in**: process independent tasks in parallel, then merge the results. Use `pipeline()` and `parallel()` only when needed.
   - **Expert Pool**: select and invoke only the specialists matching the input. Suited to sub-agents or persistent agents.
   - **Producer-Reviewer**: one agent produces, another reviews. Use the workflow's adversarial verification or a pair of persistent agents.
   - **Supervisor**: a central agent watches progress and reassigns work. Use persistent agents and a shared task list.
   - **Hierarchical Delegation**: a higher-level agent delegates further to lower-level agents. Use only within two levels, and limit workflow nesting to one level.
3. If output accuracy is critical, combine the following verification schemes.
   - **Adversarial verification**: attach N adversarial verifier agents per finding; only items that a majority judge `confirmed` with sufficient evidence pass. `refuted` or `uncertain` verdicts do not count as passing.
   - **Judge panel**: generate N drafts independently, judge them in parallel, and build the final version from the best draft.
   - **Loop-until-dry**: keep searching until newly found items are zero for K consecutive rounds.
   - **Multi-criteria sweep**: investigate in parallel across different criteria such as containers, contents, entities, and time.
   - **Completeness critic**: have the last agent look only for what's missing.

#### 2-3. Criteria for splitting agents

Split agents by the expertise required, parallelizability, conversational context that must be retained, and likelihood of reuse. See the detailed table in the "Agent separation criteria" section of `references/team-patterns.md`.

### Step 3: Write agent definitions

Specialized agents to be reused across sessions are defined as `project/.claude/agents/{name}.md` files. Don't put repeatedly used roles directly in the `Agent` tool's `prompt` only.

- Only by defining them as files can they be reused in later sessions. Invoke them with `subagent_type: "{name}"` from the `Agent` tool, or `agentType: "{name}"` from `Workflow`.
- Predefine what agents will exchange so collaboration results are stable.
- Agents describe *who* does the work; skills describe *how* it's done — don't mix the two.

Create reusable specialist roles as custom types in files, and specify that file's name in `subagent_type` or `agentType` when invoking. Don't create separate definition files for one-off tasks that use built-in types like `general-purpose`, `Explore`, or `Plan` as-is.

#### Check for overlap with existing agents

Before creating a new agent file, check whether its role overlaps with existing agents in `project/.claude/agents/`. Don't skip this check even when adding just an agent while skipping step 1 — building or extending a harness multiple times can accumulate agents with the same role under different names. If it overlaps, don't create a new name; reuse or extend the existing agent. See the decision criteria and exceptions (intentional domain specialization) in the "Agent reuse design" section of `references/team-patterns.md`.

#### Model selection criteria

Choose a model per agent based on the work's complexity, duration, autonomy, and response-speed needs. Specify it in the YAML frontmatter `model:` or in the invocation arguments `model` / `opts.model`, and record the rationale as a comment in the agent definition or the orchestrator.

| Model | Selection criteria | Representative work |
| --- | --- | --- |
| **fable** | The hardest work that must plan on its own, chain multiple steps, and run autonomously over a long period | Agent coordination, planning and long-horizon execution, synthesizing vast material, concretizing vague ideas |
| **opus** | Specialized work with a clear scope but requiring deep reasoning and analysis | Design/architecture, code generation, complex analysis, cross-verification, research-method critique, creative writing |
| **sonnet** | Routine work with clear procedures where fast turnaround matters | Log analysis, format conversion, static file inspection, running deploy scripts, simple collection, general writing and summarization |

- If the work must run autonomously over a long period while adapting the next plan to earlier results, use fable. To deeply analyze one well-scoped problem, use opus. For example, critiquing a single paper in depth suits opus; reviewing dozens of papers to produce a strategy and report suits fable.
- Default to sonnet for ambiguous general work.
- Don't assign everything fable or opus just because the agent is "important". Choose the model by the actual work profile, not the agent's status.
- Even if the top-level planning/coordination agent uses fable, pick each worker's model separately to match its own work.

> Detailed per-model criteria are in `references/model-selection-guide.md`.

#### What goes into a definition file

The YAML frontmatter must include `name` and `description`. Optionally add `tools` to restrict available tools and `model` to change the model. For read-only review/analysis agents, remove Edit and Write from `tools` so they cannot modify files.

Conversely, give Edit along with Write to agents that fix artifacts. Without Edit, even a one-line fix requires rewriting the whole file, so on large artifacts the agent gives up on edits and works around them. Also, since there are cases where tools listed in `tools` aren't actually granted at runtime, have persistent agents report the list of tools actually available in their first message.

The body must state the core role, working principles, input/output rules, error handling, and collaboration methods. For persistent agents, add a `## Communication rules` section defining `SendMessage` counterparts and shared task-list usage.

> Definition templates, full examples, and cautions on restricting `tools` are in the "Agent definition structure" section of `references/team-patterns.md`.

#### When including a QA agent

- Give the QA agent a type that can use all verification tools. `Explore` is read-only and cannot run verification scripts.
- Don't just check file existence. Compare API responses against the frontend hook response structures.
- Don't verify only once at the very end. Verify as soon as each module is completed.
- Follow the details in `references/qa-agent-guide.md`.

### Step 4: Write skills

Create each agent's skill at `project/.claude/skills/{name}/SKILL.md`. Follow `references/skill-writing-guide.md` for the detailed method.

#### 4-0. Check for overlap with existing skills

Before creating a new skill, check whether its function overlaps with existing skills in `project/.claude/skills/`. If it overlaps, don't create a new name; wire or extend the existing skill to the agent. See the decision criteria and exceptions (intentional domain specialization), and how far to generalize, in the "Skill reuse design" section of `references/skill-writing-guide.md`.

#### 4-1. Directory structure

```
skill-name/
├── SKILL.md              # required
│   ├── YAML frontmatter  # name and description required
│   └── Markdown body
├── scripts/              # optional: executable code for repeated work or work that must
│                         # always produce identical results
├── references/           # optional: reference documents read on demand
└── assets/               # optional: files used in artifacts, like templates and images
```

#### 4-2. Write trigger conditions into the description

Claude decides which skill to load by looking at the skill's `name` and `description`. The `description` should state specifically what the skill does and when it must be used, and also distinguish lookalike cases where it must not be used.

**Bad example:** `"A skill that processes PDF documents"`

**Good example:** `"Performs PDF work: reading PDF files, extracting text and tables, merging, splitting, rotating, watermarking, encryption, OCR. MUST be used whenever the user mentions a .pdf file or requests a PDF artifact."`

#### 4-3. Body writing principles

| Principle | How to apply |
| --- | --- |
| **Explain the why** | Don't just list `ALWAYS`/`NEVER`; explain why the rule exists. Knowing the reason leads to correct judgment in exceptional situations. |
| **Stay concise** | Keep `SKILL.md` under 500 lines. Delete content that doesn't aid judgment, or move it to `references/`. |
| **Generalize into principles** | Don't create rules that fit only a specific example. Write judgment criteria that apply across many inputs. |
| **Pre-place repeated code** | If multiple agents would rewrite the same script during testing, put it in `scripts/`. |
| **Write as directives** | Pick one imperative style and use it consistently throughout the document. The required actions must be unmistakable. |

#### 4-4. Load information progressively, only what's needed

A skill loads its information and executable code at the following points in time.

| Information | When it's loaded | Recommended size |
| --- | --- | --- |
| **Metadata** (`name`, `description`) | Always | ~100 words |
| **`SKILL.md` body** | When the skill is invoked | Under 500 lines |
| **`references/`** | When the material is needed | Unlimited |
| **`scripts/`** | When running repeated work or work that must always produce identical results | Unlimited; can be executed directly without reading |

- As `SKILL.md` approaches 500 lines, move details into `references/` and note in the body when to read which file.
- If a reference document exceeds 300 lines, add a table of contents near the top.
- If guidance differs per domain or framework, split reference documents so only the needed file is read.

#### 4-5. Wiring agents and skills

- One agent can use one or more skills.
- Multiple agents can share the same skill.
- Skills describe how the work is done; agents carry the role responsible for that work.

### Step 5: Integrate and define the execution order

The orchestrator is also a skill. It binds individual agents and skills into one workflow and defines who collaborates, when, and in what order. Full per-mode templates are in `references/orchestrator-template.md`, and workflow script examples are in `references/workflow-recipes.md`.

When extending an existing harness, don't create a new orchestrator; edit the existing file. When adding agents, reflect that in the composition, task assignment, and data-passing order, and add the new trigger conditions to the `description`.

#### 5-0. Orchestrators per execution mode

**A. Workflow orchestration**

Define a `Workflow` script in the orchestrator skill. The script consists of `meta`, `phase()`, `pipeline()`, `parallel()`, and `agent()`. Specify custom types with `agentType`, and receive schema-conforming results via `schema`.

```
[orchestrator skill] → Workflow(script)
    ├── phase('collect'): pipeline(items, ...)   ← fan out a pre-defined list
    ├── phase('verify'): adversarial verification or judge panel
    └── return structured results → main writes the synthesis report
```

**B. Persistent agent collaboration**

Spawn named agents, then coordinate via a shared task list and `SendMessage`. `TeamCreate` and `TeamDelete` no longer exist. No explicit team object is created; agents spawned with names in a session automatically belong to the single collaboration group that forms. You can message those agents again while they retain prior conversational context.

```
[main agent (leader)]
    ├── Agent(name: "researcher", ...) / Agent(name: "critic", ...)  ← run in parallel
    ├── TaskCreate(tasks + dependencies)
    ├── SendMessage({to: "critic"}, "review researcher's draft")
    └── collect and synthesize results
```

**C. Sub-agent delegation**

Call the `Agent` tool N times in parallel within one message and collect results from the completion notifications. Invoked agents run in the background by default.

If the nature of the work differs per phase, you can compose a hybrid mode. For example, collect material with a workflow and have persistent agents negotiate the synthesis, or adversarially verify persistent agents' output with a workflow. Label each phase with `**Execution mode:**`.

#### 5-1. Data-passing methods

| Method | Implementation | Suited execution mode | When to use |
| --- | --- | --- | --- |
| **Structured return value** | `Workflow`'s `agent(prompt, {schema})` returns validated JSON | Workflow orchestration | When the next stage must process the result in code |
| **Plain return value** | The `Agent` tool's return message | Sub-agents | When the main agent collects summary results directly |
| **Messages** | Direct agent-to-agent transfer via `SendMessage` | Persistent agents | When real-time coordination and feedback are needed |
| **Shared task list** | State sharing via `TaskCreate`, `TaskUpdate` | Persistent agents | When managing progress, dependencies, dynamic assignment |
| **Files** | Write to and read from predetermined paths | All modes | When data is large or the work process must be reviewable later |

Follow these rules when passing data through files.

- Store intermediate artifacts under `_workspace/` in the working directory.
- Use filenames of the form `{phase}_{agent}_{artifact}.{ext}`. E.g., `01_analyst_requirements.md`
- Store only the final artifacts at the user-specified path. Keep `_workspace/` for post-hoc verification.

#### 5-2. Error handling

Put an error-handling policy in the orchestrator.

- Retry once; if it fails again, proceed without that result but record the gap in the final report. Don't delete conflicting data — keep it with provenance.
- However, don't retry failures that will end the same way, such as exhausted usage limits, expired authentication, or denied permissions — retrying just burns the remaining quota. Open the partial artifacts yourself to see how far it actually got, record the missing content in a file, and report to the user. For usage limits, also tell the user when the limit resets.
- When the orchestrator fills a gap left by a stalled agent, substitute only facts you verified yourself. Never guess the agent's judgment calls (e.g., which material it excluded and why). Filling gaps with guesses amounts to forging the records needed for post-hoc verification.
- In workflows, a failed or skipped `agent()` returns `null`, and `parallel()` doesn't throw on failure. Apply `.filter(Boolean)` to result arrays and report the missing-item count via `log()`.
- If a persistent agent doesn't respond, check its status with `SendMessage` and re-instruct it. If it still fails, spawn the same custom type under a new name and pass the necessary task context in the prompt.

> For error-type-specific responses, see the "Error handling" section of the relevant execution-mode template in `references/orchestrator-template.md`.

#### 5-3. Job scale

| Job scale | Persistent agents | Workflow `Agent` call scale |
| --- | --- | --- |
| Small: under 10 tasks | 2–3 agents | 2–5 calls |
| Medium: 10–20 tasks | 3–5 agents | ~10 calls; waits automatically past the concurrency limit |
| Large: over 20 tasks | Supervisor + 3–5 workers | Dozens to hundreds of calls; overall cap 1,000 |

- More agents means more coordination overhead. Keep the default scale small.
- If the user specifies a token budget like `+500k`, the workflow script checks `budget.remaining()` to scale execution accordingly.

#### 5-4. Record harness wiring in `CLAUDE.md`

When configuration is done, record in the project's `CLAUDE.md` that a harness exists, along with its trigger conditions. `CLAUDE.md` is read every new session, so don't repeat detailed execution rules there.

````markdown
## Harness: {domain name}

**Goal:** {one line describing the harness's core objective}

**Trigger conditions:** When asked to do work related to {domain}, use the `{orchestrator-skill-name}` skill. Simple questions may be answered directly.

**Change history:**
| Date | Change | Target | Reason |
| --- | --- | --- | --- |
| {YYYY-MM-DD} | First configured with Harness v2 | All | - |
````

Don't include agent/skill lists, directory structures, or detailed execution rules. That information is managed by the orchestrator skill and `.claude/agents/`, `.claude/skills/`. Keep only trigger conditions and the change history in `CLAUDE.md`.

#### 5-5. Handling follow-up requests

The orchestrator must work not only on first run but also when results need rework.

1. Include phrases like `run again`, `re-run`, `update`, `fix`, `revise`, `redo only the {sub-task} of {domain}`, `based on the previous results`, and `improve the results` in the `description`.
2. In the orchestrator's step 0, check the existing task context.
   - If `_workspace/` exists and only part needs fixing, re-run only the relevant phase or agent.
   - If `_workspace/` exists and new input arrived, move the existing directory to a timestamped one and run fresh.
   - If `_workspace/` doesn't exist, run from scratch.
   - If the workflow's previous `runId` is available, you can resume with `resumeFromRunId`. Unchanged `agent()` calls reuse cached results.
3. Write re-invocation instructions in agent definitions. If previous result files exist, read them; if the user gave feedback, fix only the relevant parts.

### Step 6: Validation and testing

Validate the generated harness. Follow `references/skill-testing-guide.md` for details.

For a saved HarnessSpec, validate the spec before relying on it to generate runtime files. Keep validation results separate from task-quality results: a valid spec does not prove that the generated harness works.

#### 6-1. File and reference validation

- Confirm every agent file is in the right location.
- Confirm each skill's YAML frontmatter has `name` and `description`.
- Confirm the names agents use to reference each other are consistent.
- Confirm no command files were created in `.claude/commands/`.
- Confirm no v1-style `TeamCreate`, `TeamDelete`, `team_name`, or experimental flags remain in the artifacts.

#### 6-2. Per-mode validation

- **Workflow orchestration**: confirm `meta` is a literal containing only values, no `Date.now()`/`Math.random()` usage, `parallel()` used only when waiting for all results, `.filter(Boolean)` not missing, and `phase()` titles match `meta.phases`.
- **Persistent agent collaboration**: check `SendMessage` send/receive paths, task dependencies, and agent counts.
- **Sub-agent delegation**: check that each agent's input and output connect, that parallel calls are batched into one message, and that all results are collected without gaps.
- **Hybrid mode**: check that each phase states its execution mode and that data doesn't break across phase boundaries.

#### 6-3. Skill execution testing

1. For each skill, write 2–3 concrete test requests a real user might type.
2. Run with-skill and baseline executions in parallel and compare how much the skill improves results. If you need repetitions, you can even build the A/B comparison itself as a workflow.
3. Combine qualitative evaluation by direct user review with quantitative evaluation using assertions. If objective criteria can't be constructed, defer to user judgment.
4. When problems appear, don't add rules that block just one example; fix with principles that apply across situations. Re-test, and repeat until further fixes yield almost no gain.
5. If multiple agents keep recreating the same code, move it into `scripts/`.

#### 6-4. Trigger-condition validation

1. Write 10 requests that should invoke the skill, in varied phrasings and levels of explicitness.
2. Write another 10 boundary cases that sound similar but should use a different skill or tool.

Obviously unrelated requests can't validate boundaries. For example, when testing an image-generation skill, `extract the charts in this Excel file as PNGs` is a better boundary case than `write a Fibonacci function` — the result is an image, but a spreadsheet tool is actually more appropriate. Also check whether trigger conditions overlap with existing skills.

#### 6-5. Dry run

- Confirm the orchestrator's phase order is logical.
- Confirm data-passing paths don't break midway.
- Confirm every agent's input matches the previous phase's output.
- Confirm fallback procedures for errors can actually execute.

#### 6-6. Record test scenarios

Add a `## Test scenarios` section to the orchestrator skill with at least one happy path and one error path.

### Step 7: Operations, maintenance, and improvement

A harness isn't a build-once artifact.

Retrospectives on execution results and applying feedback are handled by the `evolve` skill. When the user asks to `run a harness retrospective`, `evolve the harness`, or `apply feedback`, use `evolve`. That skill analyzes the difference between the initial configuration and the current state, generalizes the feedback so it applies across situations, and applies it to agents, skills, and orchestrators. It also updates the `CLAUDE.md` change history.

This `harness` skill directly handles the following procedures for operating and maintaining an existing harness.

1. **State check**: compare `.claude/agents/`, `.claude/skills/`, and the orchestrator configuration; produce a mismatch list and inform the user.
2. **Incremental changes**: change only one item at a time and immediately run the next validation.
3. **Record changes**: write the date, change, target, and reason into `CLAUDE.md`.
4. **Verify changes**: check file structure. If trigger conditions are affected, run trigger tests too. For large changes, also run execution tests and dry runs, then do a final check that `CLAUDE.md` matches the actual files.

Propose improving via `evolve` in the following situations.

- The same kind of feedback has come up twice or more.
- Agents repeatedly fail for the same root cause.
- The user keeps handling the same task manually, bypassing the orchestrator.

## Artifact checklist

- [ ] Created files in `project/.claude/agents/` for every custom type to be reused, excluding one-off tasks that use built-in types as-is.
- [ ] Ran the clarification gate after domain analysis and the option gates before execution-mode selection and skill generation; user decisions (or "proceed unconfirmed") are recorded in the change history.
- [ ] Created the needed `SKILL.md` files and reference documents in `project/.claude/skills/`.
- [ ] A HarnessSpec is present for reusable or complex harnesses; any deliberate one-off without a saved spec has a stated reason.
- [ ] Saved specs pass the available validator, or the handoff clearly says validation was unavailable.
- [ ] Runtime outputs match the selected supported adapter, and unsupported or lossy mappings are disclosed.
- [ ] Included data-passing methods, error handling, and test scenarios in a single orchestrator skill.
- [ ] Stated which execution mode — workflow orchestration, persistent agents, or sub-agent delegation — is used; for hybrid modes, labeled each phase.
- [ ] Chose each agent's `model:` by complexity, duration, autonomy, and response speed, and recorded the rationale as comments. Did not blanket-pin every agent to the same high-end model.
- [ ] No v1-style `TeamCreate`, `TeamDelete`, or experimental flags remain in the artifacts.
- [ ] Included `.filter(Boolean)` in workflow scripts and used only literals in `meta`. Waits for all results via `parallel()` only when strictly necessary.
- [ ] Created no files in `.claude/commands/`.
- [ ] Checked new agents/skills for role overlap with existing ones before creating them. Unless intentionally domain-specialized, reused or extended overlapping ones, with no name or role conflicts.
- [ ] Wrote agent definitions, skills, the orchestrator, and `CLAUDE.md` entries in the language the user uses in conversation. Followed an explicitly specified language or the language of existing harness files when present.
- [ ] Wrote what the skill does and its trigger conditions specifically in the skill `description`, including follow-up request phrasings.
- [ ] Kept the `SKILL.md` body under 500 lines; moved details into `references/` beyond that.
- [ ] Ran it with 2–3 test sentences resembling real requests.
- [ ] Validated trigger conditions with requests that should invoke the skill and boundary cases that shouldn't.
- [ ] Recorded only trigger conditions and the change history in `CLAUDE.md`.
- [ ] The orchestrator's step 0 distinguishes first runs, follow-up runs, and partial re-runs. For workflows, it also handles the resume option.

## Reference documents

- **Execution modes in depth**: `references/execution-modes.md`
- **Model selection guide**: `references/model-selection-guide.md`
- **Team composition patterns and agent definitions**: `references/team-patterns.md`
- **Real-world team composition examples**: `references/team-examples.md`
- **Workflow script examples and cautions**: `references/workflow-recipes.md`
- **Orchestrator templates**: `references/orchestrator-template.md`
- **Skill writing guide**: `references/skill-writing-guide.md`
- **Skill testing guide**: `references/skill-testing-guide.md`
- **QA agent guide**: `references/qa-agent-guide.md`
