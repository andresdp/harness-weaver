---
name: harness
description: "Designs a harness suited to the project and creates specialist agents and the skills each agent will use. Use when the user asks to 'set up a harness', 'build a harness', 'design a harness', 'harness engineering', or 'make an agent team'. Also use when building an automation system for a new field or project, or when restructuring or extending an existing harness. Also use for requests to operate or maintain an existing harness, such as 'inspect the harness', 'audit the harness', 'harness status', or 'sync agents/skills'. For reviewing execution results and applying feedback, use the harness:evolve skill."
---

# Harness v2 — Designing Agent Teams and Skills

Design a harness suited to the project. Define each agent's role, and create the skills agents follow while they work.

## Core principles

1. Create agent definitions in `project/.claude/agents/` and skills in `project/.claude/skills/`. Agents describe who does the work; skills describe how that work is done.
2. Choose the execution mode according to the workflow. If the order and repetition conditions can be defined in code, coordinate with a workflow. If you must exchange feedback with the same specialist, use persistent agents. For work where you only need the result once, delegate to sub-agents. Detailed selection criteria are covered in step 2.
3. Choose models according to the work's complexity, duration, autonomy, and response speed. Use fable for the hardest work that requires planning and long-running autonomous execution, opus for design, code generation, complex analysis, and cross-verification, and sonnet for everyday work such as log analysis, format conversion, and simple collection. Detailed criteria are covered in step 3.
4. Record only the invocation conditions and change history in `CLAUDE.md`, so the orchestrator skill can be loaded in new sessions as well.
5. Keep reflecting what is learned from execution results into agents, skills, and `CLAUDE.md`. Reviewing and finding changes is handled by the `harness:evolve` skill.
6. Write the generated agent definitions, skills, orchestrators, and `CLAUDE.md` entries in the language the user uses in the conversation. Do not write the artifacts in English just because this skill document and the templates in `references/` are written in English. Translate the templates' headings and example phrases into that language as well. If the user specifies a language, follow it; if extending an existing harness without a specified language, follow the language of the existing files.

## Procedure

### Step 0: Check the current state

When the harness skill is loaded, first check the existing configuration.

1. Read `project/.claude/agents/`, `project/.claude/skills/`, and `project/CLAUDE.md`.
2. Choose the procedure to follow based on the current state.
   - **New build**: if the agent or skill directories don't exist or are empty, run everything from step 1.
   - **Extend existing configuration**: if agents or skills must be added to an existing harness, run only the steps needed per the table below.
   - **Operation and maintenance**: if an existing harness must be inspected, fixed, or synced, go to the operating procedure in step 7.

   | Change | Step 1 | Step 2 | Step 3 | Step 4 | Step 5 | Step 6 |
   | --- | --- | --- | --- | --- | --- | --- |
   | Add an agent | Skip and use the step 0 results | Decide only which execution mode, team, and phase to place it in | Required | When a dedicated skill is needed | Modify the orchestrator | Required |
   | Add or modify a skill | Skip | Skip | Skip | Required | When the wiring changes | Required |
   | Change structure or execution mode | Skip | Required | Only affected agents | Only affected skills | Required | Required |

3. If an existing orchestrator contains `TeamCreate`, `TeamDelete`, or `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, it is a v1 artifact. It does not work in the current runtime, so propose moving it to v2. For details, follow "Moving from v1 to v2" in `references/execution-modes.md`.
4. Compare the actual agent and skill lists against the `CLAUDE.md` entries to find mismatches.
5. Inform the user of the inspection results and the execution plan, and get confirmation.

### Step 1: Analyze the field and the work

1. Identify the project's field and goals from the user's request.
2. Divide the kinds of work needed, such as generation, verification, editing, and analysis.
3. Examine the workflow so that an execution mode can be chosen.
   - Can the list of items to process be enumerated in advance? For example: moving N files or reviewing M perspectives
   - Is an iterative procedure of verifying and re-fixing the outputs needed?
   - Do results improve when agents exchange opinions with each other?
   - Must you keep talking with the same specialist within one session?
4. Find parts that overlap or conflict with the existing agents and skills checked in step 0.
5. Examine the codebase to identify the tech stack, data models, and major modules.
6. Match the difficulty of explanations to the terms and question level the user uses. Don't use terms such as verification conditions (assertions) or JSON Schema without explanation with users who have little coding experience.

### Step 2: Design the execution mode and team structure

#### 2-1. Choosing an execution mode

Harness v2 uses three multi-agent capabilities of Claude Code. Choose one of the following modes according to the workflow.

| Execution mode | Capabilities used | Suitable work |
| --- | --- | --- |
| **Workflow coordination** | `agent()`, `pipeline()`, `parallel()`, `phase()` in a `Workflow` script | Work where the item list, verification procedure, and repetition count can be defined in code. Work that needs schema-conforming results or dozens or more `Agent` calls |
| **Persistent agent collaboration** | `Agent(name:)`, `SendMessage`, `TaskCreate`, `TaskUpdate` | Work where named specialists must repeat feedback, negotiation, and co-editing while keeping conversational context |
| **Sub-agent delegation** | A single `Agent` call. Runs in the background by default; parallel calls possible | Work where agents don't need to talk to each other and you only need the result once |

Decide in the following order.

1. If the item list, verification criteria, and repetition conditions can be expressed in code in advance, use a workflow. A fixed flow must not be left to the model's moment-to-moment judgment if it is to be re-run the same way.
2. If it is hard to define in code and agents must talk to each other or remember earlier context, use persistent agents.
3. If neither condition applies and only the result is needed, delegate to sub-agents.
4. If the nature of the work differs per phase, compose a hybrid mode. Write each phase's execution mode in the orchestrator.

Using the `Workflow` tool requires the user's explicit consent. If the user directly requested a workflow run, or the user loaded an orchestrator skill that instructs `Workflow` calls, consider that consent given. Limit default execution to a few agents, and scale up only when the user asks for a broad investigation with words like "thoroughly" or "exhaustively".

> For a comparison of execution modes, concurrency limits, schemas, token budgets, and resume conditions, see `references/execution-modes.md`.

#### 2-2. Choosing a team composition

1. Divide the work by specialty.
2. Choose the composition that fits the work from the six approaches below. Detailed criteria are in `references/team-patterns.md`.
   - **Pipeline**: receives the previous stage's result and processes in order. Suited to `pipeline()`.
   - **Distribute and integrate (fan-out/fan-in)**: processes independent tasks in parallel, then merges the results. Use `pipeline()`, and `parallel()` only when needed.
   - **Expert pool**: selects and calls only the specialists that match the input. Suited to sub-agents or persistent agents.
   - **Generate and verify**: one agent creates and another reviews. Use the workflow's adversarial verification or a pair of persistent agents.
   - **Supervisor**: a central agent watches progress and redistributes work. Use persistent agents and a shared task list.
   - **Hierarchical delegation**: a higher-level agent delegates again to lower-level agents. Use only within two levels, and limit workflow nesting to one level.
3. If the accuracy of the outputs matters, combine the following verification approaches.
   - **Adversarial verification**: attach N adversarial verifier agents to each found item, and pass only items that a majority judges `confirmed` with sufficient evidence. `refuted` or `uncertain` verdicts are not counted as passing.
   - **Judge panel**: create N drafts separately, judge them in parallel, and build the final version from the best draft.
   - **Repeat until there are no new items (Loop-until-dry)**: search until newly found items are 0 for K consecutive rounds.
   - **Search by multiple criteria**: investigate in parallel by different criteria, such as containers, contents, entities, and time.
   - **Omission reviewer**: have the last agent look only for what is missing.

#### 2-3. Criteria for splitting agents

Split agents by the expertise needed, whether parallel processing is possible, the conversational context that must be kept, and the likelihood of reuse. See the detailed table in "Agent separation criteria" in `references/team-patterns.md`.

### Step 3: Write agent definitions

Define specialist agents to be reused across sessions as `project/.claude/agents/{name}.md` files. Don't put roles that will be used repeatedly directly only into the `Agent` tool's `prompt`.

- Only when defined as files can they be reused in the next session. Call them with `subagent_type: "{name}"` in the `Agent` tool, and `agentType: "{name}"` in `Workflow`.
- Results of collaboration are stable only if what agents exchange is defined in advance.
- Write who does the work in the agent and how the work is done in the skill, so the two don't get mixed.

Create reusable specialist roles as custom types in files, and specify that file's name in `subagent_type` or `agentType` when calling. Don't create separate definition files for one-off tasks that use built-in types such as `general-purpose`, `Explore`, or `Plan` as they are.

#### Check for overlap with existing agents

Before creating a new agent file, check whether its role overlaps with existing agents in `project/.claude/agents/`. Don't skip this check even when skipping step 1 and only adding an agent. If a harness is built or extended several times, agents with the same role can pile up under different names. If it overlaps, don't create it under a new name; use or extend the existing agent. For decision criteria and exceptions (cases of intentionally specializing the domain), see "Agent reuse design" in `references/team-patterns.md`.

#### Model selection criteria

Choose a model for each agent based on the work's complexity, duration, autonomy, and response speed. Specify it in the YAML frontmatter `model:` or in the call arguments `model` and `opts.model`, and leave the reason for the choice as a comment in the agent definition or orchestrator.

| Model | Selection criteria | Representative work |
| --- | --- | --- |
| **fable** | The hardest work that must plan by itself, chain several steps, and run autonomously for a long time | Agent coordination, planning and long-running execution, integrating vast material, concretizing vague ideas |
| **opus** | Specialized work whose scope is clear but which needs deep reasoning and analysis | Design and architecture, code generation, complex analysis, cross-verification, research-method critique, creative writing |
| **sonnet** | Everyday work with a clear procedure where fast processing matters | Log analysis, format conversion, static file inspection, running deploy scripts, simple collection, general writing and summarization |

- If it must run autonomously for a long time while changing the next plan according to earlier results, use fable. To deeply analyze one problem of fixed scope, use opus. For example, opus suits deeply critiquing one paper, and fable suits reviewing dozens of papers and producing a strategy and report.
- Use sonnet as the default for general work where judgment is ambiguous.
- Don't assign everything fable or opus just because an agent is important. Choose the model by the actual nature of the work, not by the agent's status.
- Even if fable is used for the higher-level agent that handles planning and coordination, choose models separately for the lower-level workers to match each task.

> Detailed per-model criteria are in `references/model-selection-guide.md`.

#### What to put in a definition file

Always put `name` and `description` in the YAML frontmatter. If needed, add `tools` to restrict the tools used and `model` to change the model. Remove Edit and Write from the `tools` of read-only review and analysis agents so they can't change files.

Conversely, give Edit along with Write to agents that fix outputs. Without Edit, even fixing one line requires rewriting the whole file, so when an output is large the agent gives up on fixing and works around it. Also, since there are cases where tools listed in `tools` are not given at execution time, have persistent agents report the list of tools they can actually use in their first report.

In the body, always write the core role, working principles, input and output rules, error handling, and collaboration method. Add `## Communication rules` to persistent agents to define whom to exchange `SendMessage` with and how to use the shared task list.

> Definition templates, full examples, and points to watch when restricting `tools` are in "Agent definition structure" in `references/team-patterns.md`.

#### When including a QA agent

- Give the QA agent a type that can use all verification tools. `Explore` is read-only and cannot run verification scripts.
- Don't only check whether files exist. Compare API responses against the response structures of frontend hooks.
- Don't check only once after all the work is done. Check right away each time a module is completed.
- Follow `references/qa-agent-guide.md` for details.

### Step 4: Write skills

Create the skill each agent will follow at `project/.claude/skills/{name}/SKILL.md`. Follow `references/skill-writing-guide.md` for the detailed writing method.

#### 4-0. Check for overlap with existing skills

Before creating a new skill, check whether its function overlaps with existing skills in `project/.claude/skills/`. If it overlaps, don't create it under a new name; connect the existing skill to the agent or extend it. For decision criteria and exceptions (cases of intentionally specializing the domain), and how far to generalize, see "Skill reuse design" in `references/skill-writing-guide.md`.

#### 4-1. Directory structure

```
skill-name/
├── SKILL.md              # required
│   ├── YAML frontmatter  # name and description required
│   └── Markdown body
├── scripts/              # optional: executable code for work that is repeated or must always give the same result
├── references/           # optional: reference documents read only when needed
└── assets/               # optional: files used in outputs, such as templates and images
```

#### 4-2. Writing invocation conditions in the description

Claude decides which skill to load by looking at the skill's `name` and `description`. In the `description`, write specifically what the skill does and the situations in which it should be used, and also distinguish cases that look similar but where it must not be used.

**Bad example:** `"A skill that processes PDF documents"`

**Good example:** `"Performs PDF work such as reading PDF files, extracting text and tables, merging, splitting, rotating, watermarking, encryption, and OCR. Always use when the user mentions a .pdf file or requests a PDF output."`

#### 4-3. Body writing principles

| Principle | How to apply |
| --- | --- |
| **Explain the reason first** | Don't just list `ALWAYS` and `NEVER`; make clear why the rule is needed. Knowing the reason allows correct judgment even in exceptional situations. |
| **Write concisely** | Keep `SKILL.md` under 500 lines. Delete content that doesn't help judgment or move it to `references/`. |
| **Generalize into principles** | Don't make rules that fit only a specific example. Write judgment criteria that can apply to many inputs. |
| **Put repeated code in advance** | If several agents rewrite the same script during testing, put it in `scripts/`. |
| **Write as directives** | Choose one imperative form that suits the document and use it consistently. The action to take must be clearly visible. |

#### 4-4. Loading only the needed information, step by step

A skill loads the needed information and executable code at the following points.

| Information | When it is loaded | Recommended size |
| --- | --- | --- |
| **Metadata** (`name`, `description`) | Always | About 100 words |
| **`SKILL.md` body** | When the skill is loaded | Under 500 lines |
| **`references/`** | When that material is needed | No limit |
| **`scripts/`** | When running repeated work or work that must always give the same result | No limit. Can be run directly without reading its contents |

- When `SKILL.md` approaches 500 lines, move details into `references/` and write in the body when to read which file.
- If a reference document exceeds 300 lines, put a table of contents at the top of the document.
- If guidance differs by field or framework, split the reference documents so that only the needed file is read.

#### 4-5. Connecting agents and skills

- One agent can use one or more skills.
- Several agents can share the same skill.
- Write how to do the work in the skill, and the role responsible for that work in the agent.

### Step 5: Integrate and set the execution order

The orchestrator is also a skill. It ties the individual agents and skills into one workflow and defines who collaborates, when, and in what order. The full per-mode templates are in `references/orchestrator-template.md`, and workflow script examples are in `references/workflow-recipes.md`.

When extending an existing harness, don't create a new orchestrator; modify the existing file. When adding agents, reflect them in the composition, task assignment, and data-passing order, and also put new invocation conditions in the `description`.

#### 5-0. Orchestrators per execution mode

**A. Workflow coordination**

Define a `Workflow` script in the orchestrator skill. The script consists of `meta`, `phase()`, `pipeline()`, `parallel()`, and `agent()`. Specify custom types with `agentType`, and receive schema-conforming results with `schema`.

```
[orchestrator skill] → Workflow(script)
    ├── phase('collect'): pipeline(items, ...)   ← distribute a predefined list
    ├── phase('verify'): adversarial verification or judge panel
    └── return structured results → main writes the synthesis report
```

**B. Persistent agent collaboration**

Run named agents, then coordinate with a shared task list and `SendMessage`. `TeamCreate` and `TeamDelete` no longer exist. No explicit team object is created; agents run with names in a session automatically belong to the single collaboration group that forms. You can send messages again to those agents while they keep their earlier conversational context.

```
[main agent (leader)]
    ├── Agent(name: "researcher", ...) / Agent(name: "critic", ...)  ← run in parallel
    ├── TaskCreate(tasks + dependencies)
    ├── SendMessage({to: "critic"}, "review researcher's draft")
    └── collect and synthesize results
```

**C. Sub-agent delegation**

Call the `Agent` tool N times in parallel in one message and collect the results from the completion notifications. Called agents run in the background by default.

If the nature of the work differs per phase, a hybrid mode can be composed. For example, collect material with a workflow and then have persistent agents agree on the integration, or adversarially verify results produced by persistent agents with a workflow. Write `**Execution mode:**` above each phase.

#### 5-1. Data-passing methods

| Method | Implementation | Suitable execution mode | When to use |
| --- | --- | --- | --- |
| **Structured return value** | `Workflow`'s `agent(prompt, {schema})` returns validated JSON | Workflow coordination | When the next stage must process the result in code |
| **Plain return value** | The `Agent` tool's return message | Sub-agents | When the main agent collects summary results directly |
| **Messages** | Direct transfer between agents with `SendMessage` | Persistent agents | When real-time coordination and feedback are needed |
| **Shared task list** | State sharing with `TaskCreate`, `TaskUpdate` | Persistent agents | When managing progress, dependencies, and dynamic assignment |
| **Files** | Write to and read from predetermined paths | All modes | When data is large or the work process must be checked later |

When passing data through files, follow these rules.

- Store intermediate outputs in `_workspace/` under the working directory.
- Use file names of the form `{phase}_{agent}_{artifact}.{ext}`. Example: `01_analyst_requirements.md`
- Store only the final outputs in the path the user specified. Keep `_workspace/` for later verification.

#### 5-2. Error handling

Put an error-handling policy in the orchestrator.

- Retry once; if it fails again, proceed without that result, but note the omission in the final report. Don't delete conflicting data; keep it together with its source.
- However, don't retry failures that will give the same result if retried, such as exhausted usage limits, expired authentication, or denied permissions. Retrying only uses up the remaining limit. Open the partial outputs directly to check how far the work actually got, record the missing content in a file, and report to the user. For usage limits, also tell the user when the limit resets.
- When the orchestrator fills a gap left by a stopped agent, reflect only facts it has checked directly. Don't guess and fill in the agent's judgments (for example, which material it excluded and why). Filling by guesswork amounts to forging the records to be used for later verification.
- In workflows, an `agent()` that failed or was skipped returns `null`, and `parallel()` doesn't throw failures as exceptions. Apply `.filter(Boolean)` to result arrays and report the number of missing items with `log()`.
- If a persistent agent doesn't respond, check its status with `SendMessage` and instruct it again. If it still fails, run the same custom type under a new name and pass the needed task context in the prompt.

> For responses per error type, see "Error handling" in the relevant execution-mode template in `references/orchestrator-template.md`.

#### 5-3. Job scale

| Job scale | Number of persistent agents | Scale of `Agent` calls in a workflow |
| --- | --- | --- |
| Small: under 10 tasks | 2–3 | 2–5 calls |
| Medium: 10–20 tasks | 3–5 | About 10 calls. Waits automatically when the concurrency limit is exceeded |
| Large: over 20 tasks | Supervisor + 3–5 workers | Dozens to hundreds of calls. Overall limit 1,000 calls |

- The more agents there are, the higher the management cost. Keep the default scale small.
- If the user specifies a token budget such as `+500k`, check `budget.remaining()` in the workflow script to adjust the execution scale.

#### 5-4. Recording the harness connection in `CLAUDE.md`

When configuration is finished, record in the project's `CLAUDE.md` that a harness exists, along with its invocation conditions. `CLAUDE.md` is read in every new session, so don't repeat detailed execution rules there.

````markdown
## Harness: {domain name}

**Goal:** {one line describing the harness's core goal}

**Invocation conditions:** When asked to do work related to {domain}, use the `{orchestrator-skill-name}` skill. Simple questions may be answered directly.

**Change history:**
| Date | Change | Target | Reason |
| --- | --- | --- | --- |
| {YYYY-MM-DD} | First configured with Harness v2 | All | - |
````

Don't include agent and skill lists, directory structures, or detailed execution rules. That information is managed in the orchestrator skill and in `.claude/agents/` and `.claude/skills/`. Keep only invocation conditions and the change history in `CLAUDE.md`.

#### 5-5. Handling follow-up requests

The orchestrator must work not only on the first run but also when results are fixed again.

1. Put expressions such as `run again`, `re-run`, `update`, `fix`, `supplement`, `redo only the {sub-task} of {domain}`, `based on the previous results`, and `improve the results` in the `description`.
2. In the orchestrator's step 0, check the existing work context.
   - If `_workspace/` exists and the request is to fix only part, re-run only that phase or agent.
   - If `_workspace/` exists and new input was received, move the existing directory to a directory with a timestamp, then run fresh.
   - If `_workspace/` doesn't exist, run from the beginning.
   - If the workflow's previous `runId` exists, it can be resumed with `resumeFromRunId`. Unchanged `agent()` calls use cached results.
3. Write how to be re-invoked in the agent definitions. If previous result files exist, read them; if there is user feedback, fix only those parts.

### Step 6: Verification and testing

Verify the generated harness. Follow `references/skill-testing-guide.md` for the detailed method.

#### 6-1. File and reference verification

- Check that every agent file is in the correct location.
- Check that each skill's YAML frontmatter has `name` and `description`.
- Check that the names agents use to refer to each other match.
- Check that no command files were created in `.claude/commands/`.
- Check that no v1-style `TeamCreate`, `TeamDelete`, `team_name`, or experimental feature flags remain in the outputs.

#### 6-2. Verification per execution mode

- **Workflow coordination**: check that `meta` is a literal containing only values, that `Date.now()` and `Math.random()` are not used, that `parallel()` is used only when all results must be awaited, that `.filter(Boolean)` is not missing, and that `phase()` titles match `meta.phases`.
- **Persistent agent collaboration**: check the sending and receiving paths of `SendMessage`, task dependencies, and the number of agents.
- **Sub-agent delegation**: check that each agent's input and output connect, that parallel calls are bundled into one message, and that all results are collected without omission.
- **Hybrid mode**: check that each phase has its execution mode written, and that data doesn't break when phases change.

#### 6-3. Skill execution testing

1. For each skill, create 2–3 concrete test requests that a real user might enter.
2. Perform with-skill runs and baseline runs in parallel, and compare how much the skill improves the results. If repetition is needed, the A/B comparison itself can be made into a workflow.
3. Use both qualitative evaluation, which the user reviews directly, and quantitative evaluation using verification conditions (assertions). If objective conditions can't be made, follow the user's judgment.
4. When problems appear, don't add rules that block only a specific example; fix them with principles that apply to many situations. Test again, and repeat until further fixes give almost no effect.
5. If several agents repeatedly create the same code, put it in `scripts/`.

#### 6-4. Invocation condition verification

1. Create 10 requests that should load the skill, with different phrasings and levels of explicitness.
2. Also create 10 boundary cases whose wording is similar but which should use a different skill or tool.

Clearly unrelated requests can't verify the boundary. For example, when testing an image-generation skill, `extract the charts in this Excel file as PNG` is a better boundary case than `write a Fibonacci function`. The result is an image, but a spreadsheet tool is actually more suitable. Also check whether the invocation conditions overlap with existing skills.

#### 6-5. Dry run

- Check that the orchestrator's phase order is logical.
- Check that data-passing paths don't break midway.
- Check that every agent's input matches the previous phase's output.
- Check that the fallback procedure can actually be run when an error occurs.

#### 6-6. Recording test scenarios

Create `## Test scenarios` in the orchestrator skill and write at least one normal flow and one error flow.

### Step 7: Operation, maintenance, and improvement

A harness is not an output that is made once and finished.

Reviewing execution results and applying feedback is handled by the `harness:evolve` skill. When the user asks for `harness retrospective`, `harness evolution`, or `apply the feedback`, use `harness:evolve`. That skill analyzes the difference between the initial configuration and the current state, organizes the feedback so it can apply to many situations, and reflects it into agents, skills, and orchestrators. It also updates the `CLAUDE.md` change history.

This `harness` skill directly handles the following procedures for operating and maintaining an existing harness.

1. **Check the current state**: compare `.claude/agents/`, `.claude/skills/`, and the orchestrator configuration, make a list of mismatches, and inform the user.
2. **Add and modify a little at a time**: change only one item at a time and run the next verification right away.
3. **Record the change history**: write the date, change, target, and reason in `CLAUDE.md`.
4. **Verify changes**: check the file structure. If invocation conditions are affected, also run invocation tests. If the scope of change is large, run execution tests and a dry run as well, then finally check that `CLAUDE.md` and the actual files match.

Propose improving with `harness:evolve` in the following situations.

- The same kind of feedback has come up twice or more.
- Agents fail repeatedly for the same cause.
- The user keeps handling the same work manually without going through the orchestrator.

## Output checklist

- [ ] Created files in `project/.claude/agents/` for every custom type to be reused. Excluded cases that use built-in types as they are for one-off work.
- [ ] Created the needed `SKILL.md` files and reference documents in `project/.claude/skills/`.
- [ ] Put the data-passing method, error handling, and test scenarios in one orchestrator skill.
- [ ] Wrote which execution mode is used among workflow coordination, persistent agents, and sub-agents. For hybrid mode, marked each phase.
- [ ] Chose each agent's `model:` according to complexity, duration, autonomy, and response speed, and left the reason as a comment. Did not assign the same high-performance model to all agents in bulk.
- [ ] No v1-style elements such as `TeamCreate`, `TeamDelete`, or experimental feature flags remain in the outputs.
- [ ] Put `.filter(Boolean)` in workflow scripts and used only literals in `meta`. Waits for all results with `parallel()` only when truly necessary.
- [ ] Created no files in `.claude/commands/`.
- [ ] Checked whether new agents and skills overlap in role with existing ones before creating them. Unless the domain was intentionally specialized, used or extended the existing ones where they overlap, and no names or roles conflict.
- [ ] Wrote the agent definitions, skills, orchestrator, and `CLAUDE.md` entries in the language the user uses in the conversation. Followed a language the user specified, or the language of existing harness files, if present.
- [ ] Wrote what the skill should do and its invocation conditions specifically in the skill `description`, and included follow-up request expressions.
- [ ] The `SKILL.md` body is under 500 lines. If 500 lines or more, moved details into `references/`.
- [ ] Ran with 2–3 test sentences similar to real requests.
- [ ] Verified invocation conditions with requests that should load the skill and boundary cases that should not.
- [ ] Recorded only invocation conditions and the change history in `CLAUDE.md`.
- [ ] The orchestrator's step 0 distinguishes first runs, follow-up runs, and partial re-runs. Workflows also handle the resume option.

## Reference documents

- **Execution modes in detail**: `references/execution-modes.md`
- **Model selection guide**: `references/model-selection-guide.md`
- **Team composition approaches and agent definitions**: `references/team-patterns.md`
- **Practical team composition examples**: `references/team-examples.md`
- **Workflow script examples and cautions**: `references/workflow-recipes.md`
- **Orchestrator templates**: `references/orchestrator-template.md`
- **Skill writing guide**: `references/skill-writing-guide.md`
- **Skill testing guide**: `references/skill-testing-guide.md`
- **QA agent guide**: `references/qa-agent-guide.md`
